from qdrant_client import QdrantClient
from qdrant_client.http import models
from pathlib import Path
from typing import List, Dict, Any, Optional
from config import settings
import logging

logger = logging.getLogger(__name__)

class VectorStore:
    """Qdrant wrapper for managing financial data embeddings."""

    def __init__(self, db_path: Path = settings.QDRANT_PATH):
        # Using local storage mode for Qdrant
        self.client = QdrantClient(path=str(db_path))
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        self._ensure_collection()

    def _ensure_collection(self):
        """Ensure the collection exists with correct configuration."""
        collections = self.client.get_collections().collections
        exists = any(c.name == self.collection_name for c in collections)
        
        if not exists:
            logger.info(f"Creating Qdrant collection: {self.collection_name}")
            self.client.create_collection(
                collection_name=self.collection_name,
                vectors_config=models.VectorParams(
                    size=1536, # OpenAI embedding size
                    distance=models.Distance.COSINE
                )
            )

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]], ids: List[str]):
        """Add document chunks and their embeddings to Qdrant."""
        if not chunks:
            return

        points = []
        for i, (chunk, embedding, point_id) in enumerate(zip(chunks, embeddings, ids)):
            points.append(
                models.PointStruct(
                    id=i, # Qdrant local works better with integers or UUIDs
                    vector=embedding,
                    payload={
                        "content": chunk["content"],
                        "metadata": chunk.get("metadata", {}),
                        "original_id": point_id
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points to collection {self.collection_name}")

    def query(self, query_embedding: List[float], n_results: int = 5, where: Optional[Dict] = None) -> Dict[str, Any]:
        """Search for similar documents in Qdrant."""
        results = self.client.query_points(
            collection_name=self.collection_name,
            query=query_embedding,
            limit=n_results,
        ).points
        
        # Format results to match previous interface
        documents = [res.payload["content"] for res in results]
        metadatas = [res.payload["metadata"] for res in results]
        
        return {
            "documents": [documents],
            "metadatas": [metadatas]
        }

    def reset(self):
        """Reset the collection (delete and recreate)."""
        try:
            self.client.delete_collection(collection_name=self.collection_name)
            self._ensure_collection()
            logger.info(f"Collection {self.collection_name} reset.")
        except Exception as e:
            logger.warning(f"Could not reset collection: {e}")
