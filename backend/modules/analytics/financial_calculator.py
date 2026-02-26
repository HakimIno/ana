import polars as pl
from typing import Dict, Any


class FinancialCalculator:
    """Financial calculations using Polars."""

    def summary_stats(self, df: pl.DataFrame, column: str) -> Dict[str, Any]:
        """Generate statistical summary for a specific numeric column."""
        if column not in df.columns:
            raise ValueError(f"Column '{column}' not found in DataFrame.")

        dtype = df.schema[column]
        if not dtype.is_numeric():
            raise ValueError(f"Column '{column}' must be numeric.")

        stats_df = df.select([
            pl.col(column).count().alias("count"),
            pl.col(column).mean().alias("mean"),
            pl.col(column).std().alias("std"),
            pl.col(column).min().alias("min"),
            pl.col(column).quantile(0.25).alias("25%"),
            pl.col(column).median().alias("50%"),
            pl.col(column).quantile(0.75).alias("75%"),
            pl.col(column).max().alias("max"),
            pl.col(column).sum().alias("sum"),
        ])

        return stats_df.to_dicts()[0]
