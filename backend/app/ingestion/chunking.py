from functools import lru_cache
from langchain_text_splitters import RecursiveCharacterTextSplitter
from ..config import settings
from ..hyperparams import HP


@lru_cache(maxsize=1)
def get_tokenizer():
    from transformers import AutoTokenizer
    return AutoTokenizer.from_pretrained(settings.embedding_model)


def split_documents(docs, tokenizer=None):
    """Step 2/3: token-aware splitting (bge sub-word tokenizer), clause-boundary separators."""
    tok = tokenizer or get_tokenizer()
    splitter = RecursiveCharacterTextSplitter.from_huggingface_tokenizer(
        tok, chunk_size=HP.chunk_size, chunk_overlap=HP.chunk_overlap,
        separators=["\n\nSection", "\n\nClause", "\n\nRule", "\n\n", "\n", ". ", " ", ""],
    )
    chunks = splitter.split_documents(docs)
    for i, c in enumerate(chunks):
        c.metadata["chunk_id"] = f"{c.metadata['source']}::{i}"
    return chunks
