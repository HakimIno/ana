import structlog
from typing import Optional
from config import settings
from modules.rag.retriever import Retriever
from modules.llm.analyst_agent import AnalystAgent

logger = structlog.get_logger(__name__)

# Global agent and RAG components
_analyst_agent: Optional[AnalystAgent] = None
_retriever: Optional[Retriever] = None

def get_shared_retriever() -> Retriever:
    """Get or initialize the shared retriever instance."""
    global _retriever
    if _retriever is None:
        from modules.rag.embedder import Embedder
        from modules.rag.vector_store import VectorStore
        logger.info("Initializing shared retriever...")
        embedder = Embedder()
        vector_store = VectorStore()
        _retriever = Retriever(embedder=embedder, vector_store=vector_store)
    return _retriever

def get_analyst_agent() -> AnalystAgent:
    """Get or initialize the shared AnalystAgent instance."""
    global _analyst_agent
    if _analyst_agent is None:
        from api.deps import get_llm_client
        logger.info("Initializing shared analyst agent...")
        client = get_llm_client()
        retriever = get_shared_retriever()
        _analyst_agent = AnalystAgent(client=client, retriever=retriever)
    return _analyst_agent

def initialize_components():
    """Explicitly initialize components (useful for lifespan)."""
    get_analyst_agent()
