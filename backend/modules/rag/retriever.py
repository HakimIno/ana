from modules.rag.embedder import Embedder
from modules.rag.vector_store import VectorStore
from modules.rag.ranker import Ranker
import logging

logger = logging.getLogger(__name__)

class Retriever:
    """Retriever for building query context from vector store using Hybrid Search & Reranking."""

    def __init__(self, embedder: Embedder, vector_store: VectorStore, ranker: Ranker = None):
        self.embedder = embedder
        self.vector_store = vector_store
        self.ranker = ranker or Ranker()

    def get_context(self, query: str, top_k: int = 5) -> str:
        """
        Embed the query and retrieve relevant chunks using Hybrid Search & Reranking.
        """
        try:
            # 1. Embed query (Dense + Sparse)
            query_vector = self.embedder.get_embedding(query)
            query_sparse = self.embedder.get_sparse_embeddings([query])[0]
            
            # 2. Search vector store (Initial larger pool for reranking)
            search_results = self.vector_store.query(
                query_embedding=query_vector,
                query_sparse=query_sparse,
                n_results=top_k * 3 # Fetch more for reranking
            )
            
            docs = search_results.get("documents", [[]])[0]
            
            if not docs:
                return "No relevant context found."

            # 3. Rerank the results
            reranked_docs = self.ranker.rerank(
                query=query,
                documents=docs,
                top_n=top_k
            )
            
            # 4. Format into context string
            context = "\n---\n".join([str(doc) for doc in reranked_docs])
            return context
            
        except Exception as e:
            logger.error(f"Error during retrieval: {e}")
            return f"Error retrieving context: {e}"
