from unittest.mock import MagicMock
from modules.rag.embedder import Embedder

class TestEmbedder:
    """Tests for Embedder using dependency injection and mocking."""

    def test_get_embeddings(self, mocker):
        # Setup mock client
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4])
        ]
        mock_client.embeddings.create.return_value = mock_response
        
        # Inject mock client
        embedder = Embedder(client=mock_client)
        embeddings = embedder.get_embeddings(["hello", "world"])
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]
        assert embeddings[1] == [0.3, 0.4]
        mock_client.embeddings.create.assert_called_once()

    def test_get_embedding_single(self, mocker):
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.5])]
        mock_client.embeddings.create.return_value = mock_response
        
        embedder = Embedder(client=mock_client)
        emb = embedder.get_embedding("test")
        assert emb == [0.5]
        mock_client.embeddings.create.assert_called_once()

    def test_get_embeddings_empty(self, mocker):
        embedder = Embedder(client=MagicMock())
        assert embedder.get_embeddings([]) == []
