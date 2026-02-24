import multiprocessing
from typing import List, Any
from openai import OpenAI
from zai import ZaiClient
from fastembed import SparseTextEmbedding
from config import settings
import logging

logger = logging.getLogger(__name__)

class Embedder:
    """Wrapper for embeddings with batch processing support (OpenAI or Z.AI)."""
    
    _sparse_model = None
    _sparse_lock = multiprocessing.Lock()

    def __init__(self, client: Any = None, provider: str = settings.EMBEDDING_PROVIDER):
        self.provider = provider
        if client:
            self.client = client
        else:
            if provider == "zai":
                logger.info(f"Using Z.AI embeddings with model {settings.ZAI_EMBEDDING_MODEL}")
                self.client = ZaiClient(api_key=settings.ZAI_API_KEY)
            else:
                logger.info(f"Using OpenAI embeddings with model {settings.OPENAI_EMBEDDING_MODEL}")
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
        
        self.model = settings.ZAI_EMBEDDING_MODEL if provider == "zai" else settings.OPENAI_EMBEDDING_MODEL
        
        # Initialize Sparse Encoder for Hybrid Search as a Singleton
        if Embedder._sparse_model is None:
            with Embedder._sparse_lock:
                if Embedder._sparse_model is None:
                    logger.info("Initializing SparseTextEmbedding model (Splade_PP_en_v1)")
                    cpus = multiprocessing.cpu_count()
                    Embedder._sparse_model = SparseTextEmbedding(
                        model_name="prithivida/Splade_PP_en_v1",
                        threads=max(1, cpus // 2)
                    )
        
        self.sparse_model = Embedder._sparse_model

    def get_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate dense embeddings for a list of texts."""
        if not texts:
            return []
        
        try:
            response = self.client.embeddings.create(
                input=texts,
                model=self.model
            )
            # Response format is standard across both for embeddings.create
            return [data.embedding for data in response.data]
        except Exception as e:
            logger.error(f"Error generating embeddings with {self.provider}: {e}")
            raise ValueError(f"{self.provider} Embedding failed: {e}")

    def get_sparse_embeddings(self, texts: List[str]) -> List[Any]:
        """Generate sparse embeddings using FastEmbed."""
        if not texts:
            return []
        return list(self.sparse_model.embed(texts))

    def get_embedding(self, text: str) -> List[float]:
        """Generate embedding for a single text."""
        return self.get_embeddings([text])[0]
