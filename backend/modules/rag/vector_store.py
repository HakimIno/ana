from qdrant_client import QdrantClient
from qdrant_client.http import models
from pathlib import Path
from typing import List, Dict, Any
from config import settings
import logging
import uuid

import threading

logger = logging.getLogger(__name__)

class VectorStore:
    """Qdrant wrapper for managing financial data embeddings with Hybrid Search support."""
    
    _client = None # Singleton client instance
    _lock = threading.Lock() # Lock for thread-safe initialization

    @classmethod
    def clear_client(cls):
        """Reset the singleton client (useful for tests and shutdown)."""
        with cls._lock:
            if cls._client is not None:
                try:
                    logger.info("Closing Qdrant client connection")
                    cls._client.close()
                except Exception as e:
                    logger.error(f"Error closing Qdrant client: {e}")
                cls._client = None

    def __init__(self, db_path: Path = None):
        if db_path is None:
            db_path = settings.QDRANT_PATH
            
        # Using local storage mode for Qdrant with Singleton pattern (Thread-safe)
        if VectorStore._client is None:
            with VectorStore._lock:
                # Double-check inside lock
                if VectorStore._client is None:
                    logger.info(f"Opening Qdrant connection at {db_path}")
                    VectorStore._client = QdrantClient(path=str(db_path))
        
        self.client = VectorStore._client
        self.collection_name = settings.QDRANT_COLLECTION_NAME
        
        if not getattr(VectorStore, f"_collection_checked_{self.collection_name}", False):
            self._ensure_collection()
            setattr(VectorStore, f"_collection_checked_{self.collection_name}", True)

    def _ensure_collection(self):
        """Ensure the collection exists with hybrid configuration."""
        try:
            # Check if collection exists
            collection_info = self.client.get_collection(self.collection_name)
            # Check if sparse config exists
            config_params = collection_info.config.params
            has_sparse = False
            # Try multiple ways to find it (names vary by qdrant-client version)
            if hasattr(config_params, 'sparse_vectors') and config_params.sparse_vectors:
                has_sparse = True
            elif hasattr(config_params, 'sparse_vectors_config') and config_params.sparse_vectors_config:
                has_sparse = True
            elif hasattr(config_params, 'vectors') and isinstance(config_params.vectors, dict) and 'text-sparse' in config_params.vectors:
                has_sparse = True
            
            if has_sparse:
                return # All good
            
            logger.warning("Existing collection missing sparse config. Recreating...")
            self.client.delete_collection(self.collection_name)
        except Exception:
            # Collection likely doesn't exist
            logger.info(f"Collection {self.collection_name} does not exist. Creating...")

        logger.info(f"Creating Qdrant collection: {self.collection_name}")
        self.client.create_collection(
            collection_name=self.collection_name,
            vectors_config=models.VectorParams(
                size=1536, # OpenAI embedding size
                distance=models.Distance.COSINE
            ),
            sparse_vectors_config={
                "text-sparse": models.SparseVectorParams(
                    index=models.SparseIndexParams(
                        on_disk=True
                    )
                )
            }
        )

    def add_documents(self, chunks: List[Dict[str, Any]], embeddings: List[List[float]], ids: List[str], sparse_embeddings: List[Any] = None):
        """Add document chunks with both dense and sparse embeddings to Qdrant."""
        if not chunks:
            return

        points = []
        for i, (chunk, embedding, point_id) in enumerate(zip(chunks, embeddings, ids)):
            vector_data = {"": embedding}
            if sparse_embeddings and i < len(sparse_embeddings):
                sparse_vec = sparse_embeddings[i]
                vector_data["text-sparse"] = models.SparseVector(
                    indices=sparse_vec.indices.tolist(),
                    values=sparse_vec.values.tolist()
                )

            # Create a deterministic UUID from the point_id string
            # Qdrant local mode requires valid UUIDs for string IDs
            namespace = uuid.NAMESPACE_DNS
            valid_uuid = str(uuid.uuid5(namespace, str(point_id)))
            
            points.append(
                models.PointStruct(
                    id=valid_uuid,
                    vector=vector_data,
                    payload={
                        "content": chunk["content"],
                        "metadata": chunk.get("metadata", {}),
                    }
                )
            )

        self.client.upsert(
            collection_name=self.collection_name,
            points=points
        )
        logger.info(f"Upserted {len(points)} points (Hybrid) to {self.collection_name}")

    def query(self, query_embedding: List[float], query_sparse: Any = None, n_results: int = 5, filter_metadata: Dict[str, Any] = None) -> Dict[str, Any]:
        """Search using Hybrid Search (Dense + Sparse) with optional metadata filtering."""
        
        prefetch = [
            models.Prefetch(query=query_embedding, limit=n_results),
        ]
        
        if query_sparse:
            sparse_vec = models.SparseVector(
                indices=query_sparse.indices.tolist(),
                values=query_sparse.values.tolist()
            )
            prefetch.append(models.Prefetch(query=sparse_vec, using="text-sparse", limit=n_results))

        query_filter = None
        if filter_metadata:
            conditions = []
            for key, value in filter_metadata.items():
                conditions.append(
                    models.FieldCondition(
                        key=f"metadata.{key}",
                        match=models.MatchValue(value=value)
                    )
                )
            query_filter = models.Filter(must=conditions)

        results = self.client.query_points(
            collection_name=self.collection_name,
            prefetch=prefetch,
            query=models.FusionQuery(fusion=models.Fusion.RRF),
            query_filter=query_filter, # Already fixed to query_filter
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
