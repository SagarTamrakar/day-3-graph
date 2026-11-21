# PwC India: Standard vs HyDE vs Graph RAG Benchmark

LangChain + LangGraph implementation of the architecture spec. FastAPI backend, React frontend,
ChromaDB (HNSW) + NetworkX graph + BM25, bge-large-en-v1.5 embeddings (local), LLM via OpenRouter.

## Setup
```bash
cp .env.example .env            # set OPENROUTER_API_KEY (and optionally OPENROUTER_MODEL)
python -m venv .venv && .venv/bin/pip install -r backend/requirements.txt
cd backend && ../.venv/bin/uvicorn app.main:app --port 8765
cd frontend && npm install && npm run dev      # http://localhost:5173
```
The Vite dev proxy in `frontend/vite.config.ts` points `/api` at port 8000; change it if you use another backend port.
First run downloads bge-large-en-v1.5 (~1.3 GB). Sample docs for each practice area are in `data/samples/`.

## Tabs
1. Ingestion & chat (practice area, engine selector, citations) 2. 3D spherical KG (click to exclude nodes/edges)
3. LangGraph workflow (click nodes to toggle) 4. Hyperparameters & KPIs 5. Comparative benchmark.

Hyperparameters (defaults): chunk 600/60, HyDE N=3, hop k=2, RRF α=60. Tests: `cd backend && ../.venv/bin/python -m pytest`.

## Deviations from the spec
- Reranking uses embedding similarity (no cross-encoder). Node2Vec structural embeddings and Neo4j/Qdrant are not implemented; storage is behind `Store` for later swap-in.
- Latency figures in the PDF (~450/1200/850 ms) are shown as spec targets next to measured values.
