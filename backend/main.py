from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import structlog
from config import settings
from logging_config import setup_logging
from api.router import api_router
from modules.llm.analyst_agent import AnalystAgent
from modules.rag.vector_store import VectorStore
from contextlib import asynccontextmanager
from typing import Optional

logger = structlog.get_logger(__name__)

# Global agent instance
_analyst_agent: Optional[AnalystAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global _analyst_agent
    setup_logging(log_level="INFO", json_output=False)
    logger.info("starting_backend", version=settings.VERSION)
    
    # Pre-initialize AnalystAgent (loads models, connects to DB)
    # We import here to avoid circular imports with deps.py
    from api.deps import get_llm_client
    client = get_llm_client()
    _analyst_agent = AnalystAgent(client=client)
    
    yield
    # Shutdown
    logger.info("Shutting down backend...")
    VectorStore.clear_client()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AI Business Analyst Assistant",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Root endpoint
@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}", "version": settings.VERSION}

# Include the main router
app.include_router(api_router)

def get_analyst_agent():
    """Fallback for when lifespan wasn't triggered or for dependency injection."""
    global _analyst_agent
    if _analyst_agent is None:
        from api.deps import get_llm_client
        client = get_llm_client()
        _analyst_agent = AnalystAgent(client=client)
    return _analyst_agent

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
