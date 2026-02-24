import pytest
import shutil
from pathlib import Path
from modules.rag.vector_store import VectorStore

class TestVectorStore:
    """Tests for ChromaDB vector operations."""

    @pytest.fixture
    def store(self, tmp_path):
        db_path = tmp_path / "test_db"
        VectorStore.clear_client()
        vs = VectorStore(db_path=db_path)
        yield vs
        VectorStore.clear_client()
        if db_path.exists():
            shutil.rmtree(db_path)

    def test_add_and_query(self, store):
        # Use distinct directions for Cosine similarity
        vec1 = [0.0] * 1536
        vec1[0] = 1.0
        
        vec2 = [0.0] * 1536
        vec2[1] = 1.0
        
        query_vec = [0.0] * 1536
        query_vec[0] = 1.0
        query_vec[1] = 0.1 # Closer to vec1

        chunks = [
            {"content": "revenue is high", "metadata": {"id": 1}},
            {"content": "cost is low", "metadata": {"id": 2}}
        ]
        embeddings = [vec1, vec2]
        ids = ["id1", "id2"]
        
        store.add_documents(chunks, embeddings, ids)
        
        # Query for high revenue
        results = store.query(query_embedding=query_vec, n_results=1)
        assert "revenue is high" in results["documents"][0]
        assert results["metadatas"][0][0]["id"] == 1

    def test_reset(self, store):
        vec = [0.1] * 1536
        store.add_documents([{"content": "a", "metadata": {"dummy": "data"}}], [vec], ["1"])
        store.reset()
        
        # After reset, querying should return empty
        results = store.query(query_embedding=vec, n_results=1)
        assert len(results["documents"][0]) == 0
