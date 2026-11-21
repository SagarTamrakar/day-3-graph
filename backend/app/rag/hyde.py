from ..hyperparams import HP
from ..ingestion.store import get_store
from .common import synthesize, citations, Timer, rrf

ANGLES = [
    "the exact statutory / regulatory text (section, rule or master direction wording)",
    "an official circular, notification or FAQ explaining the provision in practice",
    "a contract clause, audit control or compliance procedure that implements it",
    "a case-law or enforcement perspective including penalties",
]


def run(llm, question, area, **_):
    tm = Timer()
    n = min(HP.hyde_n, len(ANGLES))
    with tm.span("llm_ms"):
        passages = [llm.invoke(
            f"Write a concise hypothetical passage (max 120 words) that would answer the question, written as {ANGLES[i]}. "
            f"Use precise domain terminology. Question: {question}").content for i in range(n)]
    store = get_store()
    with tm.span("retrieval_ms"):
        lists = [store.vector_search(p, HP.top_k, area) for p in passages]
        hits = rrf(lists, HP.rrf_alpha, HP.top_k)
    with tm.span("llm_ms"):
        answer = synthesize(llm, area, question, hits)
    return {"engine": "hyde", "answer": answer, "citations": citations(hits), "contexts": [h[1] for h in hits],
            "hyde_passages": passages, "timings": {**tm.t, "graph_ms": 0, "total_ms": sum(tm.t.values())}}
