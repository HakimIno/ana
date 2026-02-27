from fastapi import HTTPException
from openai import OpenAI
from typing import Optional
from config import settings

def get_llm_client():
    """Client for Chat/Analysis (default provider)."""
    if settings.CHAT_PROVIDER == "zai":
        from zai import ZaiClient
        return ZaiClient(api_key=settings.ZAI_API_KEY)
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def get_llm_client_for_model(model: Optional[str]):
    """Return (client, model_name) for a given model ID. Supports OpenAI, Gemini, and OpenRouter."""
    if not model:
        return get_llm_client(), settings.OPENAI_MODEL

    # OpenRouter models
    if model.startswith("openrouter/"):
        if not settings.OPENROUTER_API_KEY:
            raise HTTPException(status_code=400, detail="OPENROUTER_API_KEY not configured")
        actual_model = model.replace("openrouter/", "")
        client = OpenAI(
            api_key=settings.OPENROUTER_API_KEY,
            base_url="https://openrouter.ai/api/v1",
        )
        return client, actual_model

    gemini_models = {"gemini-2.0-flash", "gemini-1.5-pro", "gemini-1.5-flash"}
    if model in gemini_models:
        if not settings.GEMINI_API_KEY:
            raise HTTPException(status_code=400, detail="GEMINI_API_KEY not configured")
        client = OpenAI(
            api_key=settings.GEMINI_API_KEY,
            base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
        )
        return client, f"models/{model}"

    # OpenAI models (gpt-4o, gpt-4o-mini, etc.)
    return OpenAI(api_key=settings.OPENAI_API_KEY), model

def get_embedding_client():
    """Client for Embeddings (OpenAI requested)."""
    if settings.EMBEDDING_PROVIDER == "zai":
        from zai import ZaiClient
        return ZaiClient(api_key=settings.ZAI_API_KEY)
    return OpenAI(api_key=settings.OPENAI_API_KEY)

# Global agent list or cache could go here if needed, 
# for now we'll match main.py's global _analyst_agent pattern if necessary,
# but it's cleaner to handle via FastAPI dependency.

def get_analyst_agent():
    # This will be imported in main.py to handle the lifespan instance
    from main import get_analyst_agent as main_get_agent
    return main_get_agent()
