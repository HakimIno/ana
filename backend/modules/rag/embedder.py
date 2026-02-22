from typing import List, Optional
from openai import OpenAI
from config import settings
import logging

logger = logging.getLogger(__name__)

class Embedder:
    """Wrapper for OpenAI embeddings with batch processing support."""

    def __init__(self, client: Optional[OpenAI] = None, model: str = settings.EMBEDDING_MODEL):
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.model = model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for a list of texts."""
        if not texts:
            return []
        
        try:
            # Simple batching can be added here if needed for very large requests
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings: {e}")
            raise ValueError(f"OpenAI Embedding failed: {e}")

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.get_embeddings([text])[0]
