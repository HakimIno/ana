import pytest
import polars as pl
import os
from modules.data.duckdb_provider import DuckDBDataProvider

class TestDuckDBDataProvider:
    @pytest.fixture
    def provider(self, tmp_path):
        db_path = str(tmp_path / "test.duckdb")
        return DuckDBDataProvider(db_path=db_path)

    def test_load_and_query(self, provider, temp_csv_file):
        table_name = "sales_test"
        success = provider.load_file(temp_csv_file, table_name=table_name)
        assert success is True
        assert table_name in provider.tables
        
        # Test query
        df = provider.query(f"SELECT * FROM {table_name}")
        assert isinstance(df, pl.DataFrame)
        assert df.shape[0] == 4
        assert "Revenue" in df.columns

    def test_get_schema(self, provider, temp_csv_file):
        provider.load_file(temp_csv_file, table_name="financials")
        schema = provider.get_schema()
        assert "financials" in schema
        assert "Revenue" in schema["financials"]
        assert "Month" in schema["financials"]

    def test_disconnect_reconnect(self, provider, temp_csv_file):
        provider.load_file(temp_csv_file, table_name="data")
        provider.disconnect()
        assert provider.conn is None
        
        provider.reconnect()
        assert provider.conn is not None
        df = provider.query("SELECT COUNT(*) as count FROM data")
        assert df["count"][0] == 4

    def test_close_removes_file(self, provider, temp_csv_file):
        db_path = provider.db_path
        provider.load_file(temp_csv_file, table_name="temp")
        provider.close()
        assert not os.path.exists(db_path)
