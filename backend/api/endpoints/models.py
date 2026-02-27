from fastapi import APIRouter
from config import settings

router = APIRouter()

@router.get("/models")
async def list_models():
    """Return available AI models based on configured API keys."""
    models = [
        {
            "id": "gpt-4o",
            "label": "GPT-4o",
            "provider": "openai",
            "cost": "$$$",
            "enabled": bool(settings.OPENAI_API_KEY),
        },
        {
            "id": "gpt-4o-mini",
            "label": "GPT-4o Mini",
            "provider": "openai",
            "cost": "$",
            "enabled": bool(settings.OPENAI_API_KEY),
        },
        {
            "id": "gemini-2.0-flash",
            "label": "Gemini 2.0 Flash",
            "provider": "gemini",
            "cost": "Free",
            "enabled": bool(settings.GEMINI_API_KEY),
        },
        {
            "id": "openrouter/anthropic/claude-3.5-sonnet",
            "label": "Claude 3.5 Sonnet",
            "provider": "openrouter",
            "cost": "$$$",
            "enabled": bool(settings.OPENROUTER_API_KEY),
        },
        {
            "id": "openrouter/deepseek/deepseek-chat",
            "label": "DeepSeek V3",
            "provider": "openrouter",
            "cost": "$",
            "enabled": bool(settings.OPENROUTER_API_KEY),
        },
        {
            "id": "openrouter/google/gemini-pro-1.5",
            "label": "Gemini 1.5 Pro (via OR)",
            "provider": "openrouter",
            "cost": "$$",
            "enabled": bool(settings.OPENROUTER_API_KEY),
        },
        {
            "id": "openrouter/meta-llama/llama-3.1-405b-instruct",
            "label": "Llama 3.1 405B",
            "provider": "openrouter",
            "cost": "$$$",
            "enabled": bool(settings.OPENROUTER_API_KEY),
        },
        {
            "id": f"openrouter/{settings.MINIMAX_MODEL}",
            "label": "MiniMax M2.5",
            "provider": "openrouter",
            "cost": "$$",
            "enabled": bool(settings.OPENROUTER_API_KEY),
        },
    ]
    return [m for m in models if m["enabled"]]
