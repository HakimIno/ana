import pytest
import json
from modules.llm.output_parser import OutputParser


class TestOutputParser:
    """Tests for OutputParser JSON parsing and chart unification."""

    def test_valid_json_parsing(self):
        raw = json.dumps({
            "answer": "Revenue is 1M",
            "key_metrics": {"Revenue": "1M"},
            "recommendations": ["Invest"],
            "risks": ["Competition"],
            "confidence_score": 0.9,
        })
        result = OutputParser.parse_analysis(raw)
        assert result.answer == "Revenue is 1M"
        assert result.key_metrics["Revenue"] == "1M"
        assert result.confidence_score == 0.9

    def test_charts_list_parsed(self):
        raw = json.dumps({
            "answer": "See chart.",
            "charts": [{"type": "bar", "title": "Revenue", "data": [{"label": "Jan", "value": 100}]}],
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.8,
        })
        result = OutputParser.parse_analysis(raw)
        assert len(result.charts) == 1
        assert result.charts[0].type == "bar"

    def test_legacy_chart_data_merged(self):
        """Legacy chart_data should be converted into charts list."""
        raw = json.dumps({
            "answer": "See chart.",
            "chart_data": [{"label": "Jan", "value": 100}],
            "title": "Sales",
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.7,
        })
        result = OutputParser.parse_analysis(raw)
        assert len(result.charts) == 1
        assert result.charts[0].title == "Sales"
        assert result.chart_data is None  # Deprecated

    def test_malformed_json_graceful(self):
        result = OutputParser.parse_analysis("not valid json {{{")
        assert result.status == "error"
        assert "failed" in result.answer.lower()

    def test_empty_answer_preserved(self):
        raw = json.dumps({
            "answer": "",
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.5,
        })
        result = OutputParser.parse_analysis(raw)
        assert result.answer == ""

    def test_token_usage_passed(self):
        from models.response_models import TokenUsage
        usage = TokenUsage(prompt_tokens=100, completion_tokens=50, total_tokens=150)
        raw = json.dumps({
            "answer": "Test",
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.9,
        })
        result = OutputParser.parse_analysis(raw, token_usage=usage)
        assert result.token_usage.total_tokens == 150

    def test_rag_context_stored(self):
        raw = json.dumps({
            "answer": "Test",
            "key_metrics": {},
            "recommendations": [],
            "risks": [],
            "confidence_score": 0.9,
        })
        result = OutputParser.parse_analysis(raw, rag_context="Some context")
        assert result.source_documents == ["Some context"]
