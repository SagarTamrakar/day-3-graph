import json
import re

# Step 3: canonical entity normalization (synonym map).
ALIASES = {
    "cbdt": "CBDT", "central board of direct taxes": "CBDT", "income tax dept": "CBDT",
    "income tax department": "CBDT", "tax authority": "CBDT",
    "cbic": "CBIC", "central board of indirect taxes and customs": "CBIC",
    "rbi": "RBI", "reserve bank of india": "RBI",
    "sebi": "SEBI", "securities and exchange board of india": "SEBI",
    "pmla": "PMLA", "prevention of money laundering act": "PMLA",
    "gst council": "GST Council", "mac": "MAC Clause", "material adverse change": "MAC Clause",
}


def normalize(name: str) -> str:
    key = re.sub(r"\s+", " ", name.strip().lower())
    return ALIASES.get(key, name.strip())


EXTRACT_PROMPT = """Extract regulatory entities and relations from the text. Return ONLY JSON:
{{"entities":[{{"name":str,"type":str}}],"triples":[{{"subject":str,"relation":str,"object":str}}]}}
Keep legal clauses intact; use short relation verbs (issues, amends, requires, penalizes, applies_to, indemnifies).

TEXT:
{text}"""


def extract_entities(llm, text: str) -> dict:
    """LLM-guided entity-relation extraction; tolerant of malformed output."""
    try:
        raw = llm.invoke(EXTRACT_PROMPT.format(text=text[:3000])).content
        m = re.search(r"\{.*\}", raw, re.S)
        data = json.loads(m.group(0)) if m else {}
    except Exception:
        data = {}
    triples = []
    for t in data.get("triples", []):
        if all(k in t for k in ("subject", "relation", "object")):
            triples.append({"subject": normalize(str(t["subject"])), "relation": str(t["relation"]).lower(),
                            "object": normalize(str(t["object"]))})
    ents = {normalize(str(e.get("name", ""))): e.get("type", "Entity") for e in data.get("entities", []) if e.get("name")}
    return {"entities": ents, "triples": triples}
