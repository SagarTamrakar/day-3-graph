from pathlib import Path
from .loaders import load_file
from .chunking import split_documents
from .entities import extract_entities
from .store import get_store


def ingest_file(path: Path, practice_area: str, llm=None) -> dict:
    docs = load_file(path, practice_area)
    chunks = split_documents(docs)
    if llm is None:
        from ..llm import get_llm
        llm = get_llm()
    extractions = [extract_entities(llm, c.page_content) for c in chunks]
    store = get_store()
    store.add_chunks(chunks, extractions)
    return {"file": path.name, "chunks": len(chunks), **store.stats()}
