import pytest
import polars as pl
from modules.data.csv_provider import CSVDataProvider

class TestCSVDataProvider:
    @pytest.fixture
    def provider(self):
        return CSVDataProvider()

    def test_load_and_query(self, provider, temp_csv_file):
        table_name = "test_table"
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

    def test_load_invalid_file(self, provider):
        success = provider.load_file("non_existent.txt")
        assert success is False

    def test_close(self, provider, temp_csv_file):
        provider.load_file(temp_csv_file, table_name="to_clear")
        provider.close()
        assert len(provider.tables) == 0
