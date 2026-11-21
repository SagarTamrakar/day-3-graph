import networkx as nx
from app.rag.common import rrf
from app.ingestion.entities import normalize
from app.eval.kpis import context_recall, entity_resolution_accuracy
from app.eval.gold import ENTITY_GOLD


def test_rrf_alpha_60():
    a = [("x", "", {}), ("y", "", {})]
    b = [("y", "", {}), ("z", "", {})]
    out = rrf([a, b], 60, 3)
    assert out[0][0] == "y"           # y: 1/62 + 1/61 beats x: 1/61
    assert [o[0] for o in out] == ["y", "x", "z"]


def test_alias_normalization():
    assert normalize("Income Tax Dept") == normalize("Tax Authority") == "CBDT"
    assert normalize("Unknown Body") == "Unknown Body"


def test_entity_resolution_gold():
    assert entity_resolution_accuracy({k: normalize(k) for k in ENTITY_GOLD}, ENTITY_GOLD) == 1.0


def test_context_recall():
    assert context_recall(["Section 194C applies, 2% TDS"], ["194C", "2%", "xyz"]) == 2 / 3


class FakeStore:
    """Toy store reusing Store.k_hop logic without Chroma/embeddings."""
    from app.ingestion.store import Store
    k_hop = Store.k_hop

    def __init__(self):
        self.graph = nx.MultiDiGraph()
        self.graph.add_edge("A", "B", relation="issues")
        self.graph.add_edge("B", "C", relation="amends")
        self.graph.add_edge("C", "D", relation="penalizes")


def test_k_hop_radius():
    s = FakeStore()
    n1, _ = s.k_hop(["A"], 1)
    n2, _ = s.k_hop(["A"], 2)
    assert n1 == {"A", "B"} and n2 == {"A", "B", "C"}


def test_k_hop_disabled_edge():
    s = FakeStore()
    n, _ = s.k_hop(["A"], 2, disabled_edges={"B|C"})
    assert n == {"A", "B"}
