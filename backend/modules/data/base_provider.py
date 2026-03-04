from abc import ABC, abstractmethod
from typing import Dict, List, Optional
import polars as pl

class BaseDataProvider(ABC):
    """
    Abstract Base Class for all Data Providers.
    Plugins must implement these methods to be compatible with the Orchestrator.
    """

    @abstractmethod
    def load_file(self, file_path: str, table_name: Optional[str] = None) -> bool:
        """
        Load a file (CSV, Excel, Parquet) into the provider's storage.
        """
        pass

    @abstractmethod
    def query(self, sql: str) -> pl.DataFrame:
        """
        Execute a SQL query against the loaded data and return a Polars DataFrame.
        """
        pass

    @abstractmethod
    def get_schema(self) -> Dict[str, List[str]]:
        """
        Return a mapping of table names to their column names.
        """
        pass

    @abstractmethod
    def disconnect(self):
        """
        Temporarily release the database connection.
        """
        pass

    @abstractmethod
    def reconnect(self):
        """
        Re-establish the database connection.
        """
        pass

    @abstractmethod
    def close(self):
        """
        Release resources and perform cleanup.
        """
        pass
