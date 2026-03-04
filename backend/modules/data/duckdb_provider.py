import duckdb
import os
import polars as pl
from typing import Dict, List, Optional
from .base_provider import BaseDataProvider

class DuckDBDataProvider(BaseDataProvider):
    """
    High-performance Data Provider using DuckDB.
    Supports fast SQL queries and handles large datasets efficiently.
    """

    def __init__(self, db_path: str = ":memory:"):
        self.db_path = db_path
        self.conn = duckdb.connect(database=self.db_path)
        self.tables: List[str] = []

    def load_file(self, file_path: str, table_name: Optional[str] = None) -> bool:
        if not table_name:
            table_name = os.path.splitext(os.path.basename(file_path))[0]
        
        try:
            # Check if table already exists In the persistent DB and NOT empty
            try:
                table_exists = self.conn.execute(
                    f"SELECT count(*) FROM information_schema.tables WHERE table_name = '{table_name}'"
                ).fetchone()[0] > 0
                
                if table_exists:
                    # Check row count to ensure it's not a ghost table
                    row_count = self.conn.execute(f"SELECT count(*) FROM {table_name}").fetchone()[0]
                    if row_count > 0:
                        if table_name not in self.tables:
                            self.tables.append(table_name)
                        return True
            except Exception:
                pass # Table doesn't exist or isn't queryable

            # DuckDB can directly query CSV/Excel/Parquet files
            if file_path.endswith('.csv'):
                self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_csv_auto('{file_path}')")
            elif file_path.endswith('.xlsx') or file_path.endswith('.xls'):
                df = pl.read_excel(file_path)
                self.conn.register(table_name, df)
                # For Excel, we might need to materialize it if we want it to persist in the file
                self.conn.execute(f"CREATE TABLE {table_name} AS SELECT * FROM {table_name}")
            elif file_path.endswith('.parquet'):
                self.conn.execute(f"CREATE TABLE IF NOT EXISTS {table_name} AS SELECT * FROM read_parquet('{file_path}')")
            else:
                return False
            
            if table_name not in self.tables:
                self.tables.append(table_name)
            return True
        except Exception as e:
            print(f"DuckDB Load Error: {e}")
            return False

    def query(self, sql: str) -> pl.DataFrame:
        try:
            return self.conn.execute(sql).pl()
        except Exception as e:
            print(f"DuckDB Query Error: {e}")
            return pl.DataFrame()

    def get_schema(self) -> Dict[str, List[str]]:
        schema = {}
        if not self.conn:
            return schema
        
        try:
            # Query actual database catalog for all tables
            tables = self.conn.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'main'").fetchall()
            for row in tables:
                table_name = row[0]
                # Include column types so LLM knows date vs varchar
                cols_query = f"SELECT column_name, data_type FROM information_schema.columns WHERE table_name = '{table_name}' ORDER BY ordinal_position"
                columns = [f"{c[0]} ({c[1].lower()})" for c in self.conn.execute(cols_query).fetchall()]
                schema[table_name] = columns
                
                # Sync internal tracking
                if table_name not in self.tables:
                    self.tables.append(table_name)
        except Exception as e:
            print(f"DuckDB Schema Error: {e}")
            
        return schema

    def disconnect(self):
        if self.conn:
            self.conn.close()
            self.conn = None

    def reconnect(self):
        if not self.conn:
            self.conn = duckdb.connect(database=self.db_path)

    def close(self):
        if self.conn:
            self.conn.close()
            self.conn = None
        if self.db_path != ":memory:" and os.path.exists(self.db_path):
            try:
                os.remove(self.db_path)
            except Exception:
                pass
