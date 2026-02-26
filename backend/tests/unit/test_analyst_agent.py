import pytest
import json
from unittest.mock import MagicMock
import polars as pl
from modules.llm.analyst_agent import AnalystAgent
from models.response_models import AnalysisResponse


class TestAnalystAgent:
    """Tests for AnalystAgent core methods."""

    @pytest.fixture
    def mock_client(self):
        client = MagicMock()
        # Default: no usage attribute
        mock_response = MagicMock()
        mock_response.usage = None
        mock_response.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "answer": "Test answer",
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.8
        })))]
        client.chat.completions.create.return_value = mock_response
        return client

    @pytest.fixture
    def mock_retriever(self):
        retriever = MagicMock()
        retriever.get_context.return_value = "Some RAG context."
        return retriever

    @pytest.fixture
    def agent(self, mock_client, mock_retriever):
        return AnalystAgent(client=mock_client, retriever=mock_retriever)

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "Branch": ["Ari", "Siam", "Thonglor", "Ari", "Siam"],
            "Item": ["Tom Yum", "Sukiyaki", "Tom Yum", "Suki", "Mala"],
            "Revenue": [50000.0, 80000.0, 45000.0, 60000.0, 70000.0],
            "Cost": [30000.0, 50000.0, 28000.0, 35000.0, 42000.0],
            "Month": ["Jan", "Jan", "Feb", "Feb", "Mar"],
        })

    # ─────────────────────────────────────────────
    # _auto_profile_column
    # ─────────────────────────────────────────────

    def test_profile_revenue_column(self, agent, sample_df):
        profile = agent._auto_profile_column("Revenue", pl.Float64, sample_df)
        assert profile["role"] == "revenue"
        assert profile["dtype"] == "Float64"

    def test_profile_branch_column(self, agent, sample_df):
        profile = agent._auto_profile_column("Branch", pl.Utf8, sample_df)
        assert profile["role"] == "location"
        assert "unique_values" in profile
        assert set(profile["unique_values"]) == {"Ari", "Siam", "Thonglor"}

    def test_profile_unknown_column(self, agent, sample_df):
        profile = agent._auto_profile_column("xyz_random", pl.Float64, sample_df)
        assert profile["role"] == "unknown"

    def test_profile_thai_column(self, agent):
        df = pl.DataFrame({"ยอดขาย": [100, 200]})
        profile = agent._auto_profile_column("ยอดขาย", pl.Int64, df)
        assert profile["role"] == "revenue"

    def test_profile_high_cardinality(self, agent):
        """Columns with >15 unique values should show count + sample, not full list."""
        df = pl.DataFrame({"ProductName": [f"Product_{i}" for i in range(25)]})
        profile = agent._auto_profile_column("ProductName", pl.Utf8, df)
        assert profile["role"] == "name"
        assert "unique_count" in profile
        assert profile["unique_count"] == 25
        assert len(profile["sample_values"]) == 10

    # ─────────────────────────────────────────────
    # _profile_dataframe
    # ─────────────────────────────────────────────

    def test_profile_dataframe_with_samples(self, agent, sample_df):
        result = agent._profile_dataframe("test", sample_df, include_samples=True)
        assert result["records"] == 5
        assert "sample_data" in result
        assert len(result["sample_data"]) == 3
        assert "column_profile" in result
        assert "Branch" in result["column_profile"]

    def test_profile_dataframe_without_samples(self, agent, sample_df):
        result = agent._profile_dataframe("test", sample_df, include_samples=False)
        assert "sample_data" not in result

    def test_profile_dataframe_has_dimension_values(self, agent, sample_df):
        result = agent._profile_dataframe("test", sample_df)
        assert "dimension_values" in result
        assert "Branch" in result["dimension_values"]

    # ─────────────────────────────────────────────
    # _prepare_metrics_context
    # ─────────────────────────────────────────────

    def test_prepare_metrics_with_dfs(self, agent, sample_df):
        result = agent._prepare_metrics_context(dfs={"sales": sample_df})
        parsed = json.loads(result)
        assert "active_dataframes" in parsed
        assert "sales" in parsed["active_dataframes"]

    def test_prepare_metrics_with_data_list(self, agent):
        data = [{"Month": "Jan", "Revenue": 100000}, {"Month": "Feb", "Revenue": 120000}]
        result = agent._prepare_metrics_context(data=data)
        parsed = json.loads(result)
        assert "dataset_scope" in parsed

    def test_prepare_metrics_no_data(self, agent):
        result = agent._prepare_metrics_context()
        assert result == "No data available."

    def test_prepare_metrics_join_keys(self, agent):
        df1 = pl.DataFrame({"Branch": ["A"], "Revenue": [100]})
        df2 = pl.DataFrame({"Branch": ["A"], "Cost": [50]})
        result = agent._prepare_metrics_context(dfs={"sales": df1, "costs": df2})
        parsed = json.loads(result)
        assert "suggested_join_keys" in parsed
        keys = parsed["suggested_join_keys"]
        assert any("Branch" in v for v in keys.values())

    # ─────────────────────────────────────────────
    # _build_history_text
    # ─────────────────────────────────────────────

    def test_build_history_truncation(self, agent):
        agent.memory = MagicMock()
        long_content = "A" * 500
        agent.memory.get_history.return_value = [
            {"role": "user", "content": long_content},
        ]
        result = agent._build_history_text("test_session")
        assert "[TRUNCATED]" in result
        assert len(result) < 500

    # ─────────────────────────────────────────────
    # analyze (integration-level with mocks)
    # ─────────────────────────────────────────────

    def test_analyze_returns_response(self, agent, mock_client):
        data = [{"Month": "Jan", "Revenue": 100000}]
        result = agent.analyze("How is revenue?", data_context=data)
        assert isinstance(result, AnalysisResponse)
        assert result.answer == "Test answer"

    def test_analyze_error_handling(self, agent, mock_client):
        mock_client.chat.completions.create.side_effect = Exception("LLM Down")
        result = agent.analyze("test")
        assert result.status == "error"
        assert "failed" in result.answer.lower()

    def test_analyze_with_code_execution(self, agent, mock_client):
        """Test the 2-turn flow: code gen → execute → refine."""
        # Turn 1: returns code
        turn1 = MagicMock()
        turn1.usage = None
        turn1.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "answer": "",
            "python_code": "print('hello')",
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.9
        })))]

        # Turn 2: returns final answer
        turn2 = MagicMock()
        turn2.usage = None
        turn2.choices = [MagicMock(message=MagicMock(content=json.dumps({
            "answer": "Analysis complete.",
            "key_metrics": {"total": 100},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.95
        })))]

        mock_client.chat.completions.create.side_effect = [turn1, turn2]

        data = [{"Month": "Jan", "Revenue": 100000}]
        result = agent.analyze("Analyze revenue", data_context=data)
        assert result.answer == "Analysis complete."
        assert result.python_code == "print('hello')"
