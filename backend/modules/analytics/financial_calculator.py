import polars as pl
from typing import List, Dict, Any

class FinancialCalculator:
    """Production-grade financial calculations using Polars."""

    def gross_profit(self, revenue: float, cost: float) -> float:
        """Calculate Gross Profit = Revenue - Cost of Goods Sold."""
        return float(revenue - cost)

    def gross_margin(self, revenue: float, cost: float) -> float:
        """Calculate Gross Margin % = (Gross Profit / Revenue) * 100."""
        if revenue == 0:
            raise ValueError("Revenue cannot be zero for margin calculation.")
        profit = self.gross_profit(revenue, cost)
        return float((profit / revenue) * 100)

    def net_profit(self, gross_profit: float, expenses: float) -> float:
        """Calculate Net Profit = Gross Profit - Operating Expenses."""
        return float(gross_profit - expenses)

    def net_margin(self, net_profit: float, revenue: float) -> float:
        """Calculate Net Margin % = (Net Profit / Revenue) * 100."""
        if revenue == 0:
            raise ValueError("Revenue cannot be zero for margin calculation.")
        return float((net_profit / revenue) * 100)

    def growth_rate(self, current: float, previous: float) -> float:
        """Calculate Growth Rate % = ((Current - Previous) / Previous) * 100."""
        if previous == 0:
            if current == 0:
                return 0.0
            raise ValueError("Previous value cannot be zero for growth rate calculation.")
        return float(((current - previous) / previous) * 100)

    def roi(self, gain: float, cost: float) -> float:
        """Calculate Return on Investment % = ((Gain - Cost) / Cost) * 100."""
        if cost == 0:
            raise ValueError("Investment cost cannot be zero for ROI calculation.")
        return float(((gain - cost) / cost) * 100)

    def break_even_point(self, fixed_costs: float, price_per_unit: float, variable_cost_per_unit: float) -> float:
        """Calculate Break-even point (units) = Fixed Costs / (Price - Variable Cost)."""
        contribution_margin = price_per_unit - variable_cost_per_unit
        if contribution_margin <= 0:
            raise ValueError("Price per unit must be greater than variable cost per unit.")
        return float(fixed_costs / contribution_margin)

    def moving_average(self, data: List[float], window: int) -> List[float]:
        """Calculate moving average for a time series using Polars."""
        if not data:
            return []
        if window <= 0:
            raise ValueError("Window size must be positive.")
        
        series = pl.Series("data", data)
        ma = series.rolling_mean(window_size=window, min_samples=1)
        return ma.to_list()

    def summary_stats(self, df: pl.DataFrame, column: str) -> Dict[str, Any]:
        """Generate statistical summary for a specific column using Polars."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")
        
        dtype = df.schema[column]
        if not dtype.is_numeric():
            raise ValueError(f"Column '{column}' must be numeric.")

        # Polars summary stats
        stats_df = df.select([
            pl.col(column).count().alias("count"),
            pl.col(column).mean().alias("mean"),
            pl.col(column).std().alias("std"),
            pl.col(column).min().alias("min"),
            pl.col(column).quantile(0.25).alias("25%"),
            pl.col(column).median().alias("50%"),
            pl.col(column).quantile(0.75).alias("75%"),
            pl.col(column).max().alias("max"),
            pl.col(column).sum().alias("sum")
        ])
        
        return stats_df.to_dicts()[0]
