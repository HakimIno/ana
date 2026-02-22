import pytest
from modules.analytics.financial_calculator import FinancialCalculator

class TestFinancialCalculator:
    """Tests for FinancialCalculator — all math verified against specs."""

    def test_gross_profit_standard_case(self, calculator):
        """Revenue minus cost equals gross profit."""
        result = calculator.gross_profit(revenue=100_000, cost=70_000)
        assert result == 30_000

    def test_gross_margin_percentage(self, calculator):
        """Gross margin = (profit / revenue) * 100."""
        result = calculator.gross_margin(revenue=100_000, cost=70_000)
        assert result == pytest.approx(30.0, rel=1e-4)

    def test_gross_margin_zero_revenue_raises(self, calculator):
        """Cannot calculate margin on zero revenue."""
        with pytest.raises(ValueError, match="Revenue cannot be zero"):
            calculator.gross_margin(revenue=0, cost=50_000)

    def test_net_profit_standard_case(self, calculator):
        result = calculator.net_profit(gross_profit=30_000, expenses=15_000)
        assert result == 15_000

    def test_net_margin_percentage(self, calculator):
        result = calculator.net_margin(net_profit=15_000, revenue=100_000)
        assert result == 15.0

    def test_growth_rate_positive(self, calculator):
        """Growth rate between Jan and Feb."""
        result = calculator.growth_rate(current=120_000, previous=100_000)
        assert result == 20.0

    def test_growth_rate_negative(self, calculator):
        """Decline should return negative percentage."""
        result = calculator.growth_rate(current=80_000, previous=100_000)
        assert result == -20.0

    def test_growth_rate_zero_previous_raises(self, calculator):
        with pytest.raises(ValueError, match="Previous value cannot be zero"):
            calculator.growth_rate(current=100, previous=0)

    def test_growth_rate_both_zero(self, calculator):
        assert calculator.growth_rate(current=0, previous=0) == 0.0

    def test_roi_calculation(self, calculator):
        result = calculator.roi(gain=150, cost=100)
        assert result == 50.0

    def test_roi_zero_cost_raises(self, calculator):
        with pytest.raises(ValueError, match="Investment cost cannot be zero"):
            calculator.roi(gain=100, cost=0)

    def test_break_even_point(self, calculator):
        # fixed=1000, price=10, variable=5 -> Contribution=5. BEP = 1000/5 = 200
        result = calculator.break_even_point(1000, 10, 5)
        assert result == 200

    def test_break_even_invalid_margin_raises(self, calculator):
        with pytest.raises(ValueError, match="Price per unit must be greater than variable cost"):
            calculator.break_even_point(1000, 5, 10)

    def test_moving_average(self, calculator):
        data = [10, 20, 30, 40]
        result = calculator.moving_average(data, window=2)
        assert result[0] == 10  # First point
        assert result[1] == 15  # (10+20)/2
        assert result[2] == 25  # (20+30)/2

    def test_summary_stats(self, calculator, sample_financial_df):
        stats = calculator.summary_stats(sample_financial_df, "Revenue")
        assert stats["count"] == 4
        assert stats["sum"] == 455000.0
        assert stats["max"] == 140000.0

    def test_summary_stats_missing_column(self, calculator, sample_financial_df):
        with pytest.raises(ValueError, match="Column 'Unknown' not found"):
            calculator.summary_stats(sample_financial_df, "Unknown")
