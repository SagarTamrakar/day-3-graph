"""Graph RAG as a LangGraph cyclic state graph:
query_expansion -> hybrid_search -(loop while hop<k)-> rrf_fusion -> rerank -> synthesis."""
import time
from typing import TypedDict, Any
from langgraph.graph import StateGraph, END
from ..hyperparams import HP
from ..ingestion.store import get_store
from .common import synthesize, citations, rrf

NODES = ["query_expansion", "hybrid_search", "rrf_fusion", "rerank", "synthesis"]


class State(TypedDict, total=False):
    question: str
    area: str
    expanded: list[str]
    seeds: list[str]
    frontier_nodes: list[str]
    hop: int
    vector_hits: list
    bm25_hits: list
    graph_hits: list
    fused: list
    final: list
    answer: str
    graph_nodes: list[str]
    trace: list
    timings: dict
    cfg: dict      # {disabled_nodes:[workflow nodes], disabled_edges:[...], kg_disabled_nodes:[], kg_disabled_edges:[]}


def _tick(state, name, start):
    state["trace"] = state.get("trace", []) + [name]
    t = state.get("timings", {})
    t[name] = t.get(name, 0) + (time.perf_counter() - start) * 1000
    state["timings"] = t


def build(llm):
    store = get_store()

    def disabled(s, n):
        return n in s.get("cfg", {}).get("disabled_nodes", [])

    def query_expansion(s: State) -> State:
        t0 = time.perf_counter()
        s["hop"], s["expanded"] = 0, [s["question"]]
        if not disabled(s, "query_expansion"):
            try:
                alt = llm.invoke("Rewrite this question once using precise regulatory terminology and any "
                                 f"synonyms for named authorities. Output only the rewrite.\n{s['question']}").content.strip()
                s["expanded"].append(alt)
            except Exception:
                pass
        s["seeds"] = list(dict.fromkeys(e for q in s["expanded"] for e in store.match_entities(q)))
        s["frontier_nodes"] = []
        _tick(s, "query_expansion", t0)
        return s

    def hybrid_search(s: State) -> State:
        t0 = time.perf_counter()
        cfg = s.get("cfg", {})
        if s["hop"] == 0:
            s["vector_hits"] = [h for q in s["expanded"] for h in store.vector_search(q, HP.top_k, s["area"])]
            s["bm25_hits"] = [h for q in s["expanded"] for h in store.bm25_search(q, HP.top_k)]
            s["graph_hits"], s["graph_nodes"] = [], []
        # one graph hop per loop iteration (cyclic edge)
        g0 = time.perf_counter()
        kg_n, kg_e = set(cfg.get("kg_disabled_nodes", [])), set(cfg.get("kg_disabled_edges", []))
        seeds = [x for x in s["seeds"] if x not in kg_n]
        nodes, _ = store.k_hop(seeds, s["hop"] + 1, kg_n, kg_e) if seeds else (set(), [])
        s["graph_nodes"] = sorted(nodes)
        ids = store.chunk_ids_for_nodes(nodes)
        s["graph_hits"] = [(i, store.chunks[i]["text"], store.chunks[i]["metadata"]) for i in ids if i in store.chunks]
        s["timings"] = {**s.get("timings", {}), "graph_ms": s.get("timings", {}).get("graph_ms", 0) + (time.perf_counter() - g0) * 1000}
        s["hop"] += 1
        _tick(s, "hybrid_search", t0)
        return s

    def more_hops(s: State) -> str:
        if disabled(s, "hybrid_search") or not s["seeds"]:
            return "rrf_fusion"
        return "hybrid_search" if s["hop"] < HP.hop_k else "rrf_fusion"

    def rrf_fusion(s: State) -> State:
        t0 = time.perf_counter()
        lists = [s["vector_hits"], s["bm25_hits"], s["graph_hits"]]
        s["fused"] = rrf(lists, HP.rrf_alpha, HP.top_k * 2)
        _tick(s, "rrf_fusion", t0)
        return s

    def rerank(s: State) -> State:
        t0 = time.perf_counter()
        fused = s["fused"]
        if disabled(s, "rerank") or len(fused) <= HP.top_k:
            s["final"] = fused[:HP.top_k]
        else:  # embedding-similarity rerank against the question
            import numpy as np
            q = np.array(store.emb.embed_query(s["question"]))
            d = np.array(store.emb.embed_documents([h[1] for h in fused]))
            order = np.argsort(-(d @ q))[:HP.top_k]
            s["final"] = [fused[i] for i in order]
        _tick(s, "rerank", t0)
        return s

    def synthesis(s: State) -> State:
        t0 = time.perf_counter()
        extra = ""
        if s.get("graph_nodes"):
            extra = "KNOWLEDGE-GRAPH ENTITIES IN SCOPE: " + ", ".join(s["graph_nodes"][:40]) + "\n\n"
        s["answer"] = synthesize(llm, s["area"], s["question"], s["final"], extra)
        _tick(s, "synthesis", t0)
        return s

    g = StateGraph(State)
    for name, fn in zip(NODES, [query_expansion, hybrid_search, rrf_fusion, rerank, synthesis]):
        g.add_node(name, fn)
    g.set_entry_point("query_expansion")
    g.add_edge("query_expansion", "hybrid_search")
    g.add_conditional_edges("hybrid_search", more_hops, {"hybrid_search": "hybrid_search", "rrf_fusion": "rrf_fusion"})
    g.add_edge("rrf_fusion", "rerank")
    g.add_edge("rerank", "synthesis")
    g.add_edge("synthesis", END)
    return g.compile()


def run(llm, question, area, cfg: dict | None = None, **_):
    t0 = time.perf_counter()
    out = build(llm).invoke({"question": question, "area": area, "cfg": cfg or {}, "trace": [], "timings": {}})
    total = (time.perf_counter() - t0) * 1000
    tm = out["timings"]
    graph_ms = tm.get("graph_ms", 0)
    llm_ms = tm.get("query_expansion", 0) + tm.get("synthesis", 0)
    return {"engine": "graph", "answer": out["answer"], "citations": citations(out["final"]),
            "contexts": [h[1] for h in out["final"]], "trace": out["trace"], "graph_nodes": out["graph_nodes"],
            "seeds": out["seeds"],
            "timings": {"retrieval_ms": max(total - llm_ms - graph_ms, 0), "graph_ms": graph_ms, "llm_ms": llm_ms,
                        "total_ms": total, "per_node": {k: v for k, v in tm.items() if k != "graph_ms"}}}
