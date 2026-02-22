from typing import List, Dict, Any, Optional
from modules.rag.embedder import Embedder
from modules.rag.vector_store import VectorStore
import logging

logger = logging.getLogger(__name__)

class Retriever:
    """Retriever for building query context from vector store."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore):
        self.embedder = embedder
        self.vector_store = vector_store

    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Embed the query and retrieve relevant chunks, returned as a single context string.
        """
        try:
            # 1. Embed query
            query_vector = self.embedder.get_embedding(query)
            
            # 2. Search vector store
            results = self.vector_store.query(
                query_embedding=query_vector,
                n_results=top_k
            )
            
            # 3. Format into context string
            # Qdrant response format from our vector_store.py: {"documents": [ [list of strings] ], "metadatas": [ [list of dicts] ]}
            docs = results.get("documents", [[]])[0]
            
            if not docs:
                return "No relevant context found."
            
            context = "\n---\n".join(docs)
            return context
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return f"Error retrieving context: {e}"
