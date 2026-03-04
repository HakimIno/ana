import os
import polars as pl
from typing import Dict, List, Optional
from .base_provider import BaseDataProvider

class CSVDataProvider(BaseDataProvider):
    """
    Data Provider for CSV files using Polars.
    Acts as a fallback or for smaller datasets where a full DB isn't needed.
    """

    def __init__(self):
        self.tables: Dict[str, pl.DataFrame] = {}

    def load_file(self, file_path: str, table_name: Optional[str] = None) -> bool:
        if not table_name:
            table_name = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            # We use Polars to read the CSV
            df = pl.read_csv(file_path)
            self.tables[table_name] = df
            return True
        except Exception:
            return False

    def query(self, sql: str) -> pl.DataFrame:
        try:
            # Polars has a built-in SQL engine for DataFrames
            ctx = pl.SQLContext(register_globals=True)
            for name, df in self.tables.items():
                ctx.register(name, df)
            return ctx.execute(sql).collect()
        except Exception as e:
            print(f"CSV Query Error: {e}")
            return pl.DataFrame()

    def get_schema(self) -> Dict[str, List[str]]:
        return {name: df.columns for name, df in self.tables.items()}

    def disconnect(self):
        pass

    def reconnect(self):
        pass

    def close(self):
        self.tables.clear()
