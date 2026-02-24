from fastembed.rerank.cross_encoder import TextCrossEncoder
from typing import List
import logging
from config import settings

logger = logging.getLogger(__name__)

class Ranker:
    """Re-ranking layer using FastEmbed TextCrossEncoder for higher precision."""
    
    def __init__(self, model_name: str = "BAAI/bge-reranker-base"):
        logger.info(f"Initializing FastEmbed Reranker with model: {model_name}")
        # Use persistent cache directory from settings
        self.model = TextCrossEncoder(model_name=model_name, cache_dir=str(settings.FASTEMBED_CACHE_PATH))

    def rerank(self, query: str, documents: List[str], top_n: int = 5) -> List[str]:
        """Rerank search results based on actual query relevance."""
        if not documents:
            return []
            
        # FastEmbed rerank returns an iterator of scores/indices
        # Typical usage: model.rerank(query, documents)
        results = list(self.model.rerank(query, documents))
        
        # Sort by score descending
        # Results can be objects with .score or potentially different structures depending on library version
        try:
            sorted_results = sorted(results, key=lambda x: getattr(x, 'score', 0.0), reverse=True)
            top_results = [getattr(res, 'document', res) for res in sorted_results[:top_n]]
        except Exception:
            # Fallback if result structure is unexpected
            top_results = documents[:top_n]
            
        return top_results
