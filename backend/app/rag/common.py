import time
from langchain_core.messages import SystemMessage, HumanMessage
from ..prompts import system_prompt


def rrf(rank_lists: list[list[tuple]], alpha: int, top_n: int):
    """Reciprocal Rank Fusion: score(d) = sum 1/(alpha + rank). Items are (id, text, meta)."""
    scores, items = {}, {}
    for lst in rank_lists:
        for rank, it in enumerate(lst, start=1):
            scores[it[0]] = scores.get(it[0], 0.0) + 1.0 / (alpha + rank)
            items[it[0]] = it
    order = sorted(scores, key=lambda i: -scores[i])[:top_n]
    return [items[i] for i in order]


def synthesize(llm, area: str, question: str, hits: list[tuple], extra: str = "") -> str:
    ctx = "\n\n".join(f"[S{i}] (source: {m.get('source')}, p.{m.get('page')})\n{t}" for i, (_, t, m) in enumerate(hits, 1))
    msg = f"CONTEXT:\n{ctx}\n\n{extra}QUESTION: {question}"
    return llm.invoke([SystemMessage(content=system_prompt(area)), HumanMessage(content=msg)]).content


def citations(hits):
    return [{"label": f"S{i}", "chunk_id": cid, "source": m.get("source"), "page": m.get("page"), "text": t[:400]}
            for i, (cid, t, m) in enumerate(hits, 1)]


class Timer:
    def __init__(self):
        self.t = {}

    def span(self, name):
        timer = self

        class _S:
            def __enter__(s):
                s.s = time.perf_counter()

            def __exit__(s, *a):
                timer.t[name] = timer.t.get(name, 0) + (time.perf_counter() - s.s) * 1000
        return _S()
