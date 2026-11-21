from langchain_openai import ChatOpenAI
from .config import settings


def get_llm(temperature: float = 0.0) -> ChatOpenAI:
    if not settings.openrouter_api_key:
        raise RuntimeError("OPENROUTER_API_KEY is not set (copy .env.example to .env)")
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=temperature,
    )
