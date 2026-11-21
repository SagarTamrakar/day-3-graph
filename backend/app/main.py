import shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from .config import settings
from .hyperparams import HP
from .prompts import PRACTICE_AREAS
from .rag.graph_rag import NODES

app = FastAPI(title="PwC India RAG Benchmark")
app.add_middleware(CORSMiddleware, allow_origins=["http://localhost:5173"], allow_methods=["*"], allow_headers=["*"])
LAST_BENCH: dict = {}
LAST_RUN: dict = {}


class ChatReq(BaseModel):
    question: str
    area: str = "tax"
    engine: str = "graph"
    cfg: dict = {}


class HPReq(BaseModel):
    chunk_size: int | None = None
    chunk_overlap: int | None = None
    hyde_n: int | None = None
    hop_k: int | None = None
    rrf_alpha: int | None = None
    top_k: int | None = None


@app.get("/api/meta")
def meta():
    return {"areas": PRACTICE_AREAS, "engines": ["standard", "hyde", "graph"], "workflow_nodes": NODES}


@app.post("/api/ingest")
def ingest(file: UploadFile = File(...), area: str = Form("tax")):
    from .ingestion.pipeline import ingest_file
    if area not in PRACTICE_AREAS:
        raise HTTPException(400, "unknown practice area")
    up = settings.data_dir / "uploads"
    up.mkdir(parents=True, exist_ok=True)
    dest = up / Path(file.filename).name   # strip any path components
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return ingest_file(dest, area)


@app.post("/api/chat")
def chat(req: ChatReq):
    from .eval.benchmark import run_engine
    if req.engine not in ("standard", "hyde", "graph"):
        raise HTTPException(400, "unknown engine")
    try:
        res = run_engine(req.engine, req.question, req.area, req.cfg)
    except RuntimeError as e:
        raise HTTPException(500, str(e))
    LAST_RUN[req.engine] = res["timings"]
    return res


@app.get("/api/graph")
def graph():
    from .ingestion.store import get_store
    return get_store().export_graph()


@app.get("/api/stats")
def stats():
    from .ingestion.store import get_store
    return get_store().stats()


@app.post("/api/reset")
def reset():
    from .ingestion.store import get_store
    get_store().reset()
    return {"ok": True}


@app.get("/api/hyperparams")
def get_hp():
    return HP.dict()


@app.put("/api/hyperparams")
def put_hp(req: HPReq):
    return HP.update(**req.model_dump()).dict()


@app.get("/api/metrics")
def metrics():
    return {"hyperparams": HP.dict(), "last_run_timings": LAST_RUN, "benchmark": LAST_BENCH.get("summary"),
            "entity_resolution_accuracy": LAST_BENCH.get("entity_resolution_accuracy")}


@app.post("/api/benchmark")
def benchmark():
    from .eval.benchmark import run_benchmark
    res = run_benchmark()
    LAST_BENCH.clear(); LAST_BENCH.update(res)
    return res
