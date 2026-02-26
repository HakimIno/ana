import pytest
import polars as pl
from modules.analytics.financial_calculator import FinancialCalculator


class TestFinancialCalculator:
    """Tests for FinancialCalculator (only summary_stats remains)."""

    @pytest.fixture
    def calculator(self):
        return FinancialCalculator()

    @pytest.fixture
    def sample_df(self):
        return pl.DataFrame({
            "Month": ["Jan", "Feb", "Mar", "Apr"],
            "Revenue": [100000.0, 120000.0, 95000.0, 140000.0],
        })

    def test_summary_stats(self, calculator, sample_df):
        stats = calculator.summary_stats(sample_df, "Revenue")
        assert stats["count"] == 4
        assert stats["sum"] == 455000.0
        assert stats["min"] == 95000.0
        assert stats["max"] == 140000.0

    def test_summary_stats_missing_column(self, calculator, sample_df):
        with pytest.raises(ValueError, match="not found"):
            calculator.summary_stats(sample_df, "Profit")

    def test_summary_stats_non_numeric(self, calculator, sample_df):
        with pytest.raises(ValueError, match="must be numeric"):
            calculator.summary_stats(sample_df, "Month")
