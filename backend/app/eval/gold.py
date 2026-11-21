# Gold questions mapped to the sample corpus in data/samples. category: keyword | multihop | vocab
GOLD = [
    {"id": "q1", "category": "keyword", "area": "tax", "question": "What is the TDS rate under Section 194C for payments to a company contractor?",
     "facts": ["194C", "2%"]},
    {"id": "q2", "category": "multihop", "area": "tax", "question": "Which authority issued the circular amending the e-invoicing threshold, and what penalty applies for non-compliance?",
     "facts": ["CBIC", "e-invoic", "penalty"]},
    {"id": "q3", "category": "vocab", "area": "grc", "question": "What must a bank do when a customer's identity documents cannot be verified?",
     "facts": ["KYC", "RBI"]},
    {"id": "q4", "category": "multihop", "area": "deals", "question": "Which indemnity obligations are triggered if a material adverse change occurs before closing under the SPA?",
     "facts": ["indemn", "material adverse change"]},
]
ENTITY_GOLD = {"Income Tax Dept": "CBDT", "Tax Authority": "CBDT", "Reserve Bank of India": "RBI"}
