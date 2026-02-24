import pytest
from unittest.mock import MagicMock
from modules.rag.retriever import Retriever

class TestRetriever:
    """Tests for Retriever logic with mocked dependencies."""

    @pytest.fixture
    def mock_embedder(self):
        return MagicMock()

    @pytest.fixture
    def mock_vector_store(self):
        return MagicMock()

    @pytest.fixture
    def mock_ranker(self):
        return MagicMock()

    @pytest.fixture
    def retriever(self, mock_embedder, mock_vector_store, mock_ranker):
        return Retriever(embedder=mock_embedder, vector_store=mock_vector_store, ranker=mock_ranker)

    def test_get_context_success(self, retriever, mock_embedder, mock_vector_store, mock_ranker):
        # 1. Setup mocks
        mock_embedder.get_embedding.return_value = [0.1, 0.2]
        mock_embedder.get_sparse_embeddings.return_value = [MagicMock()]
        mock_vector_store.query.return_value = {
            "documents": [["Relevant chunk 1", "Relevant chunk 2"]],
            "metadatas": [[{"id": 1}, {"id": 2}]]
        }
        mock_ranker.rerank.return_value = ["Relevant chunk 1", "Relevant chunk 2"]
        
        # 2. Call method
        context = retriever.get_context("How is revenue?")
        
        # 3. Assertions
        assert "Relevant chunk 1" in context
        assert "Relevant chunk 2" in context
        assert "---" in context
        mock_embedder.get_embedding.assert_called_once_with("How is revenue?")
        mock_vector_store.query.assert_called_once()

    def test_get_context_no_results(self, retriever, mock_embedder, mock_vector_store):
        mock_embedder.get_embedding.return_value = [0.1]
        mock_vector_store.query.return_value = {"documents": [[]]}
        
        context = retriever.get_context("Empty query")
        assert context == "No relevant context found."

    def test_get_context_error(self, retriever, mock_embedder):
        mock_embedder.get_embedding.side_effect = Exception("API Down")
        
        context = retriever.get_context("Break me")
        assert "Error retrieving context" in context
