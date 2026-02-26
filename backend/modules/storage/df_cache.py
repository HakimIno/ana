"""In-memory DataFrame cache with auto-invalidation."""
import logging
from typing import Dict, Optional
import polars as pl

logger = logging.getLogger(__name__)


class DataFrameCache:
    """Caches parsed DataFrames to avoid re-parsing CSV/Excel on every query."""

    _instance: Optional["DataFrameCache"] = None
    _cache: Dict[str, pl.DataFrame] = {}

    def __new__(cls):
        """Singleton pattern — one cache for the entire app."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._cache = {}
        return cls._instance

    def get(self, filename: str) -> Optional[pl.DataFrame]:
        """Get cached DataFrame or None."""
        return self._cache.get(filename)

    def put(self, filename: str, df: pl.DataFrame) -> None:
        """Store DataFrame in cache."""
        self._cache[filename] = df
        logger.info(f"Cached DataFrame for '{filename}' ({len(df)} rows)")

    def invalidate(self, filename: str) -> None:
        """Remove a specific file from cache."""
        if filename in self._cache:
            del self._cache[filename]
            logger.info(f"Invalidated cache for '{filename}'")

    def clear(self) -> None:
        """Clear entire cache."""
        self._cache.clear()
        logger.info("Cleared entire DataFrame cache")

    def get_or_parse(self, filename: str, parser, file_path: str) -> pl.DataFrame:
        """Get from cache or parse and cache."""
        cached = self.get(filename)
        if cached is not None:
            logger.debug(f"Cache HIT for '{filename}'")
            return cached

        logger.debug(f"Cache MISS for '{filename}', parsing...")
        result = parser.parse_file(file_path)
        df = pl.DataFrame(result["data"])
        self.put(filename, df)
        return df
