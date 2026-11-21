import networkx as nx
from types import SimpleNamespace
from app.ingestion.store import Store
from app.rag import graph_rag
from app.hyperparams import HP


class FakeEmb:
    def embed_query(self, t): return [1.0, 0.0]
    def embed_documents(self, ts): return [[1.0, 0.0] for _ in ts]


class FakeStore:
    k_hop = Store.k_hop
    chunk_ids_for_nodes = Store.chunk_ids_for_nodes
    match_entities = lambda self, q: [n for n in self.graph.nodes if n.lower() in q.lower()]

    def __init__(self):
        self.emb = FakeEmb()
        self.graph = nx.MultiDiGraph()
        for n, c in [("CBIC", "c1"), ("E-Invoicing", "c2"), ("Penalty", "c3")]:
            self.graph.add_node(n, chunks=[c], type="E")
        self.graph.add_edge("CBIC", "E-Invoicing", relation="issues", chunk_id="c1")
        self.graph.add_edge("E-Invoicing", "Penalty", relation="penalizes", chunk_id="c2")
        self.chunks = {c: {"text": f"text {c}", "metadata": {"source": "s", "page": 0}} for c in ("c1", "c2", "c3")}

    def vector_search(self, q, k, area=None): return []
    def bm25_search(self, q, k): return []


class FakeLLM:
    def invoke(self, x):
        return SimpleNamespace(content="answer [S1]")


def test_two_hops_reach_penalty(monkeypatch):
    monkeypatch.setattr(graph_rag, "get_store", lambda: FakeStore())
    HP.hop_k = 2
    out = graph_rag.run(FakeLLM(), "What does CBIC require?", "tax")
    assert out["trace"].count("hybrid_search") == 2          # cyclic loop ran k times
    assert "Penalty" in out["graph_nodes"]
    assert out["trace"][-1] == "synthesis"


def test_hop_radius_one(monkeypatch):
    monkeypatch.setattr(graph_rag, "get_store", lambda: FakeStore())
    HP.hop_k = 1
    out = graph_rag.run(FakeLLM(), "What does CBIC require?", "tax")
    HP.hop_k = 2
    assert "Penalty" not in out["graph_nodes"]


def test_disabled_query_expansion_passthrough(monkeypatch):
    monkeypatch.setattr(graph_rag, "get_store", lambda: FakeStore())
    out = graph_rag.run(FakeLLM(), "CBIC?", "tax", cfg={"disabled_nodes": ["query_expansion"]})
    assert out["answer"]
