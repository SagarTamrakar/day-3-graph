import json
from pathlib import Path
from langchain_core.documents import Document


def load_file(path: Path, practice_area: str) -> list[Document]:
    """Step 1: parse PDF/DOCX/JSON/TXT into Documents with provenance metadata."""
    suffix = path.suffix.lower()
    base = {"source": path.name, "practice_area": practice_area}
    if suffix == ".pdf":
        try:
            from langchain_community.document_loaders import UnstructuredPDFLoader
            docs = UnstructuredPDFLoader(str(path), mode="elements").load()
        except Exception:  # unstructured not installed -> pypdf fallback
            from langchain_community.document_loaders import PyPDFLoader
            docs = PyPDFLoader(str(path)).load()
    elif suffix == ".docx":
        from langchain_community.document_loaders import Docx2txtLoader
        docs = Docx2txtLoader(str(path)).load()
    elif suffix == ".json":
        data = json.loads(path.read_text())
        rows = data if isinstance(data, list) else [data]
        docs = [Document(page_content=json.dumps(r, indent=1)) for r in rows]
    else:
        docs = [Document(page_content=path.read_text(errors="ignore"))]
    for i, d in enumerate(docs):
        d.metadata = {**base, "page": d.metadata.get("page", i)}
    return docs
