from fastapi.testclient import TestClient
from unittest.mock import MagicMock
from main import app
import os
import io
import json

client = TestClient(app)

class TestQueryFlow:
    """Integration tests for the full upload-to-query flow."""

    def test_full_flow_success(self, tmp_path):
        """Test uploading a file and then querying it."""
        from modules.rag.vector_store import VectorStore
        from config import settings
        
        # Override storage for test (update both env and settings object)
        test_db_path = tmp_path / "qdrant"
        os.environ["QDRANT_PATH"] = str(test_db_path)
        settings.QDRANT_PATH = test_db_path
        
        VectorStore.clear_client()
        
        # 1. Setup Mocks
        mock_openai_client = MagicMock()
        
        # Mock Embeddings
        mock_emb_response = MagicMock()
        mock_emb_response.data = [MagicMock(embedding=[0.1] * 1536)]
        mock_openai_client.embeddings.create.return_value = mock_emb_response
        
        # Mock Chat Completion
        mock_llm_response = MagicMock()
        llm_json = {
            "answer": "The profit is high.",
            "key_metrics": {"Profit": "High"},
            "recommendations": ["Expand"],
            "risks": ["Competition"],
            "confidence_score": 0.9
        }
        mock_llm_response.choices = [MagicMock(message=MagicMock(content=json.dumps(llm_json)))]
        mock_openai_client.chat.completions.create.return_value = mock_llm_response
        
        # 2. Inject Dependency Override
        from main import get_embedding_client, get_llm_client
        app.dependency_overrides[get_embedding_client] = lambda: mock_openai_client
        app.dependency_overrides[get_llm_client] = lambda: mock_openai_client
        
        try:
            client = TestClient(app)

            # 3. Create a dummy CSV file
            csv_content = "Month,Revenue,Cost\nJan,100,70\nFeb,120,80"
            files = {"file": ("test.csv", io.BytesIO(csv_content.encode()), "text/csv")}

            # 4. Perform Upload
            upload_resp = client.post("/upload", files=files)
            assert upload_resp.status_code == 200
            assert "job_id" in upload_resp.json()

            # 5. Perform Query
            query_resp = client.post("/query", json={"question": "How is the profit?"})
            assert query_resp.status_code == 200
            assert "profit" in query_resp.json()["answer"].lower()
        
            # Verify LLM was called with the correct prompt context containing metrics
            mock_openai_client.chat.completions.create.assert_called_once()
            args, kwargs = mock_openai_client.chat.completions.create.call_args
            prompt_content = kwargs["messages"][1]["content"]
            assert "revenue" in prompt_content
            assert "cost" in prompt_content
        finally:
            app.dependency_overrides.clear()

    def test_root_endpoint(self):
        response = client.get("/")
        assert response.status_code == 200
        assert "AI Business Analyst" in response.json()["message"]
