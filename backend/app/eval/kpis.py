import json
import re


def context_recall(contexts: list[str], facts: list[str]) -> float:
    """RCR: share of ground-truth facts (case-insensitive substrings) present in retrieved chunks."""
    if not facts:
        return 0.0
    blob = " ".join(contexts).lower()
    return sum(f.lower() in blob for f in facts) / len(facts)


def faithfulness(llm, answer: str, contexts: list[str]) -> float:
    """Ratio of answer claims supported by the retrieved context, judged by the LLM (0.0-1.0)."""
    prompt = ("List each factual claim in the ANSWER and mark whether the CONTEXT supports it. Return ONLY JSON: "
              '{"claims":[{"claim":str,"supported":bool}]}\n\nCONTEXT:\n' + "\n---\n".join(contexts) + "\n\nANSWER:\n" + answer)
    try:
        m = re.search(r"\{.*\}", llm.invoke(prompt).content, re.S)
        claims = json.loads(m.group(0))["claims"]
        return sum(bool(c["supported"]) for c in claims) / len(claims) if claims else 0.0
    except Exception:
        return 0.0


def entity_resolution_accuracy(predicted: dict[str, str], gold: dict[str, str]) -> float:
    """Accuracy of surface-form -> canonical-entity links versus a labelled gold map."""
    if not gold:
        return 0.0
    return sum(predicted.get(k) == v for k, v in gold.items()) / len(gold)
