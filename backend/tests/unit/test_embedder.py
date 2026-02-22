from unittest.mock import MagicMock, patch
from modules.rag.embedder import Embedder

class TestEmbedder:
    """Tests for Embedder with OpenAI mocking."""

    @patch("modules.rag.embedder.OpenAI")
    def test_get_embeddings(self, mock_openai):
        # Setup mock
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        mock_response = MagicMock()
        mock_response.data = [
            MagicMock(embedding=[0.1, 0.2]),
            MagicMock(embedding=[0.3, 0.4])
        ]
        mock_client.embeddings.create.return_value = mock_response
        
        embedder = Embedder(api_key="fake")
        embeddings = embedder.get_embeddings(["hello", "world"])
        
        assert len(embeddings) == 2
        assert embeddings[0] == [0.1, 0.2]
        mock_client.embeddings.create.assert_called_once()

    @patch("modules.rag.embedder.OpenAI")
    def test_get_embedding_single(self, mock_openai):
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_response = MagicMock()
        mock_response.data = [MagicMock(embedding=[0.5])]
        mock_client.embeddings.create.return_value = mock_response
        
        embedder = Embedder(api_key="fake")
        emb = embedder.get_embedding("test")
        assert emb == [0.5]
