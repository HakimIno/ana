import pytest
import json
from unittest.mock import MagicMock
from modules.llm.analyst_agent import AnalystAgent
from models.response_models import AnalysisResponse

class TestAnalystAgent:
    """Tests for AnalystAgent logic and LLM orchestration."""

    @pytest.fixture
    def mock_client(self):
        return MagicMock()

    @pytest.fixture
    def mock_retriever(self):
        retriever = MagicMock()
        retriever.get_context.return_value = "Verified revenue is 1M."
        return retriever

    @pytest.fixture
    def agent(self, mock_client, mock_retriever):
        return AnalystAgent(client=mock_client, retriever=mock_retriever)

    def test_analyze_structured_output(self, agent, mock_client):
        # 1. Setup mock LLM response
        llm_json = {
            "answer": "Revenue is stable.",
            "key_metrics": {"Revenue": "1M"},
            "recommendations": ["Hold"],
            "risks": ["Competition"],
            "confidence_score": 0.9
        }
        
        mock_response = MagicMock()
        mock_response.choices = [
            MagicMock(message=MagicMock(content=json.dumps(llm_json)))
        ]
        mock_client.chat.completions.create.return_value = mock_response
        
        # 2. Call analyze
        data_context = [{"Month": "Jan", "Revenue": 1000000}]
        result = agent.analyze("How is revenue?", data_context=data_context)
        
        # 3. Assertions
        assert isinstance(result, AnalysisResponse)
        assert result.answer == "Revenue is stable."
        assert result.key_metrics["Revenue"] == "1M"
        assert result.confidence_score == 0.9
        
        # 4. Verify prompt content (The "No Math" rule)
        args, kwargs = mock_client.chat.completions.create.call_args
        prompt = kwargs["messages"][1]["content"]
        
        # Check that pre-calculated metrics are in the prompt
        assert "Revenue" in prompt
        assert "1000000" in prompt # JSON raw number

    def test_analyze_error_handling(self, agent, mock_client):
        mock_client.chat.completions.create.side_effect = Exception("LLM Down")
        
        result = agent.analyze("test")
        assert result.status == "error"
        assert "error during analysis" in result.answer.lower()
