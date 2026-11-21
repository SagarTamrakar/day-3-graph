from ..llm import get_llm
from ..rag import standard, hyde, graph_rag
from ..ingestion.entities import normalize
from .kpis import context_recall, faithfulness, entity_resolution_accuracy
from .gold import GOLD, ENTITY_GOLD

ENGINES = {"standard": standard.run, "hyde": hyde.run, "graph": graph_rag.run}


def run_engine(engine: str, question: str, area: str, cfg=None, llm=None):
    return ENGINES[engine](llm or get_llm(), question, area, cfg=cfg)


def run_benchmark(engines=("standard", "hyde", "graph")):
    llm = get_llm()
    rows, agg = [], {e: {"rcr": [], "faith": [], "latency": [], "retrieval": [], "graph": [], "llm": []} for e in engines}
    for g in GOLD:
        for e in engines:
            r = ENGINES[e](llm, g["question"], g["area"])
            rcr = context_recall(r["contexts"], g["facts"])
            fa = faithfulness(llm, r["answer"], r["contexts"])
            t = r["timings"]
            rows.append({"id": g["id"], "category": g["category"], "engine": e, "rcr": rcr, "faithfulness": fa, "latency_ms": t["total_ms"]})
            a = agg[e]
            a["rcr"].append(rcr); a["faith"].append(fa); a["latency"].append(t["total_ms"])
            a["retrieval"].append(t["retrieval_ms"]); a["graph"].append(t["graph_ms"]); a["llm"].append(t["llm_ms"])
    avg = lambda xs: sum(xs) / len(xs) if xs else 0.0
    summary = {e: {"rcr": avg(a["rcr"]), "faithfulness": avg(a["faith"]), "latency_ms": avg(a["latency"]),
                   "retrieval_ms": avg(a["retrieval"]), "graph_ms": avg(a["graph"]), "llm_ms": avg(a["llm"])} for e, a in agg.items()}
    era = entity_resolution_accuracy({k: normalize(k) for k in ENTITY_GOLD}, ENTITY_GOLD)
    return {"summary": summary, "rows": rows, "entity_resolution_accuracy": era}
