"""Steps 4-6: dual index (Chroma HNSW + NetworkX adjacency + BM25) with persistence."""
import json
import re
from functools import lru_cache
import networkx as nx
from rank_bm25 import BM25Okapi
from ..config import settings
from .entities import ALIASES


@lru_cache(maxsize=1)
def get_embeddings():
    from langchain_huggingface import HuggingFaceEmbeddings
    return HuggingFaceEmbeddings(model_name=settings.embedding_model,
                                 encode_kwargs={"normalize_embeddings": True})


def tokenize(text: str):
    return re.findall(r"\w+", text.lower())


class Store:
    def __init__(self, embeddings=None):
        from langchain_chroma import Chroma
        self.emb = embeddings or get_embeddings()
        self.vs = Chroma(collection_name="chunks", embedding_function=self.emb,
                         persist_directory=str(settings.data_dir / "chroma"),
                         collection_metadata={"hnsw:space": "cosine"})
        self.graph = nx.MultiDiGraph()
        self.chunks: dict[str, dict] = {}   # chunk_id -> {text, metadata}
        self._bm25 = None
        self._load()

    # ---- indexing
    def add_chunks(self, chunks, extractions):
        self.vs.add_documents(chunks, ids=[c.metadata["chunk_id"] for c in chunks])
        for c, ex in zip(chunks, extractions):
            cid = c.metadata["chunk_id"]
            self.chunks[cid] = {"text": c.page_content, "metadata": c.metadata}
            for name, typ in ex["entities"].items():
                self._node(name, typ, cid)
            for t in ex["triples"]:
                self._node(t["subject"], "Entity", cid)
                self._node(t["object"], "Entity", cid)
                self.graph.add_edge(t["subject"], t["object"], relation=t["relation"], chunk_id=cid)
        self._bm25 = None
        self._save()

    def _node(self, name, typ, cid):
        if name not in self.graph:
            self.graph.add_node(name, type=typ, chunks=[])
        if cid not in self.graph.nodes[name]["chunks"]:
            self.graph.nodes[name]["chunks"].append(cid)

    # ---- retrieval
    def vector_search(self, query: str, k: int, area: str | None = None):
        flt = {"practice_area": area} if area else None
        res = self.vs.similarity_search_with_score(query, k=k, filter=flt)
        return [(d.metadata["chunk_id"], d.page_content, d.metadata) for d, _ in res]

    def bm25_search(self, query: str, k: int):
        if not self.chunks:
            return []
        if self._bm25 is None:
            self._ids = list(self.chunks)
            self._bm25 = BM25Okapi([tokenize(self.chunks[i]["text"]) for i in self._ids])
        scores = self._bm25.get_scores(tokenize(query))
        top = sorted(range(len(scores)), key=lambda i: -scores[i])[:k]
        return [(self._ids[i], self.chunks[self._ids[i]]["text"], self.chunks[self._ids[i]]["metadata"])
                for i in top if scores[i] > 0]

    def match_entities(self, query: str) -> list[str]:
        q = query.lower()
        found = [n for n in self.graph.nodes if n.lower() in q]
        for alias, canon in ALIASES.items():
            if re.search(rf"\b{re.escape(alias)}\b", q) and canon in self.graph and canon not in found:
                found.append(canon)
        return found

    def k_hop(self, seeds, k, disabled_nodes=(), disabled_edges=()):
        """Breadth-first k-hop expansion over the undirected view; returns (nodes, edges)."""
        seen, frontier, edges = set(seeds), set(seeds), []
        for _ in range(k):
            nxt = set()
            for n in frontier:
                for u, v, d in list(self.graph.out_edges(n, data=True)) + list(self.graph.in_edges(n, data=True)):
                    if f"{u}|{v}" in disabled_edges or u in disabled_nodes or v in disabled_nodes:
                        continue
                    edges.append((u, v, d))
                    for x in (u, v):
                        if x not in seen:
                            nxt.add(x)
            seen |= nxt
            frontier = nxt
        return seen, edges

    def chunk_ids_for_nodes(self, nodes):
        out = []
        for n in nodes:
            out += self.graph.nodes[n]["chunks"]
        return list(dict.fromkeys(out))

    # ---- graph export for UI
    def export_graph(self):
        return {"nodes": [{"id": n, "type": d.get("type", "Entity"), "degree": self.graph.degree(n)} for n, d in self.graph.nodes(data=True)],
                "links": [{"source": u, "target": v, "relation": d["relation"], "id": f"{u}|{v}"} for u, v, d in self.graph.edges(data=True)]}

    def stats(self):
        return {"chunks": len(self.chunks), "nodes": self.graph.number_of_nodes(), "edges": self.graph.number_of_edges()}

    # ---- persistence
    def _save(self):
        settings.data_dir.mkdir(exist_ok=True)
        (settings.data_dir / "graph.json").write_text(json.dumps({
            "graph": nx.node_link_data(self.graph, edges="links"), "chunks": self.chunks}, default=str))

    def _load(self):
        p = settings.data_dir / "graph.json"
        if p.exists():
            d = json.loads(p.read_text())
            self.graph = nx.node_link_graph(d["graph"], multigraph=True, directed=True, edges="links")
            self.chunks = d["chunks"]

    def reset(self):
        self.vs.delete_collection()
        from langchain_chroma import Chroma
        self.vs = Chroma(collection_name="chunks", embedding_function=self.emb,
                         persist_directory=str(settings.data_dir / "chroma"),
                         collection_metadata={"hnsw:space": "cosine"})
        self.graph, self.chunks, self._bm25 = nx.MultiDiGraph(), {}, None
        self._save()


_store = None


def get_store() -> Store:
    global _store
    if _store is None:
        _store = Store()
    return _store
