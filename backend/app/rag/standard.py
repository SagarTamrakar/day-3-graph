from ..hyperparams import HP
from ..ingestion.store import get_store
from .common import synthesize, citations, Timer


def run(llm, question, area, **_):
    tm = Timer()
    with tm.span("retrieval_ms"):
        hits = get_store().vector_search(question, HP.top_k, area)
    with tm.span("llm_ms"):
        answer = synthesize(llm, area, question, hits)
    return {"engine": "standard", "answer": answer, "citations": citations(hits), "contexts": [h[1] for h in hits],
            "timings": {**tm.t, "graph_ms": 0, "total_ms": sum(tm.t.values())}}
