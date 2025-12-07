from langchain_openai import ChatOpenAI

from app.core.config import settings


def get_llm() -> ChatOpenAI:
    """Konfiguracja klienta OpenRouter kompatybilnego z OpenAI/ChatOpenAI."""
    return ChatOpenAI(
        model=settings.openrouter_model,
        api_key=settings.openrouter_api_key,
        base_url=settings.openrouter_base_url,
        temperature=0,
        timeout=60,  # wolne/free modele często odpowiadają >20s
        max_retries=2,
        default_headers={
            "HTTP-Referer": settings.referer,
            "X-Title": settings.x_title,
        },
    )


