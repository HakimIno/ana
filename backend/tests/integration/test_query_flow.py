from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock
from main import app
import os
import io

client = TestClient(app)

class TestQueryFlow:
    """Integration tests for the full upload-to-query flow."""

    def test_full_flow_success(self, tmp_path):
        """Test uploading a file and then querying it."""
        # Override storage for test
        os.environ["STORAGE_DIR"] = str(tmp_path / "uploads")
        os.environ["VECTOR_STORE_DIR"] = str(tmp_path / "vectors")
        
        # 1. Mock OpenAI for both Embedder and Agent
        with patch("modules.rag.embedder.OpenAI") as mock_emb_openai, \
             patch("modules.llm.analyst_agent.OpenAI") as mock_agent_openai:
            
            # Setup Embedder Mock
            mock_emb_client = MagicMock()
            mock_emb_openai.return_value = mock_emb_client
            def mock_create(*args, **kwargs):
                texts = kwargs.get("input", [])
                resp = MagicMock()
                resp.data = [MagicMock(embedding=[0.1] * 1536) for _ in texts]
                return resp
            mock_emb_client.embeddings.create.side_effect = mock_create

            # Setup Agent Mock
            mock_agent_client = MagicMock()
            mock_agent_openai.return_value = mock_agent_client
            mock_llm_response = MagicMock()
            mock_llm_response.choices = [MagicMock(message=MagicMock(content="The profit is high."))]
            mock_agent_client.chat.completions.create.return_value = mock_llm_response

            client = TestClient(app)

            # 3. Create a dummy CSV file
            csv_content = "Month,Revenue,Cost\nJan,100,70\nFeb,120,80"
            files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}

            # 4. Perform Upload
            upload_resp = client.post("/upload", files=files)
            assert upload_resp.status_code == 200

            # 5. Perform Query
            query_resp = client.post("/query", json={"question": "How is the profit?"})
            assert query_resp.status_code == 200
            assert "profit" in query_resp.json()["answer"].lower()
        
            # Verify LLM was called with the correct prompt context containing metrics
            mock_agent_client.chat.completions.create.assert_called_once()
            args, kwargs = mock_agent_client.chat.completions.create.call_args
            prompt_content = kwargs["messages"][1]["content"]
            assert "revenue" in prompt_content
            assert "cost" in prompt_content

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Business Analyst" in response.json()["message"]
