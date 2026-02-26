import pytest
import polars as pl
from unittest.mock import MagicMock
from modules.storage.df_cache import DataFrameCache


class TestDataFrameCache:
    """Tests for DataFrame singleton cache."""

    @pytest.fixture(autouse=True)
    def reset_cache(self):
        """Reset singleton cache before each test."""
        DataFrameCache._instance = None
        DataFrameCache._cache = {}
        yield
        DataFrameCache._instance = None
        DataFrameCache._cache = {}

    def test_singleton(self):
        cache1 = DataFrameCache()
        cache2 = DataFrameCache()
        assert cache1 is cache2

    def test_put_and_get(self):
        cache = DataFrameCache()
        df = pl.DataFrame({"A": [1, 2, 3]})
        cache.put("test.csv", df)
        result = cache.get("test.csv")
        assert result is not None
        assert result.shape == (3, 1)

    def test_get_miss(self):
        cache = DataFrameCache()
        assert cache.get("missing.csv") is None

    def test_invalidate(self):
        cache = DataFrameCache()
        cache.put("test.csv", pl.DataFrame({"A": [1]}))
        cache.invalidate("test.csv")
        assert cache.get("test.csv") is None

    def test_clear(self):
        cache = DataFrameCache()
        cache.put("a.csv", pl.DataFrame({"A": [1]}))
        cache.put("b.csv", pl.DataFrame({"B": [2]}))
        cache.clear()
        assert cache.get("a.csv") is None
        assert cache.get("b.csv") is None

    def test_get_or_parse_cache_hit(self):
        cache = DataFrameCache()
        df = pl.DataFrame({"A": [1, 2]})
        cache.put("test.csv", df)

        mock_parser = MagicMock()  # Should NOT be called
        result = cache.get_or_parse("test.csv", mock_parser, "/fake/path")
        assert result.shape == (2, 1)
        mock_parser.parse_file.assert_not_called()

    def test_get_or_parse_cache_miss(self):
        cache = DataFrameCache()
        mock_parser = MagicMock()
        mock_parser.parse_file.return_value = {"data": [{"A": 1}, {"A": 2}]}

        result = cache.get_or_parse("test.csv", mock_parser, "/fake/path")
        assert result.shape == (2, 1)
        mock_parser.parse_file.assert_called_once_with("/fake/path")

        # Second call should be cached
        result2 = cache.get_or_parse("test.csv", mock_parser, "/fake/path")
        assert mock_parser.parse_file.call_count == 1  # Still 1
