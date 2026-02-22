import pytest
import os
from modules.ingestion.excel_parser import ExcelParser

class TestExcelParser:
    """Tests for ExcelParser — ingestion, cleaning, and detection."""

    def test_get_sheet_names_excel(self, parser, temp_excel_file):
        sheets = parser.get_sheet_names(temp_excel_file)
        assert "Q1_Data" in sheets

    def test_get_sheet_names_csv(self, parser, temp_csv_file):
        sheets = parser.get_sheet_names(temp_csv_file)
        assert sheets == ["default"]

    def test_clean_column_name(self, parser):
        assert parser.clean_column_name("Gross Revenue (USD)") == "gross_revenue_usd"
        assert parser.clean_column_name("Sheet Name! 2024") == "sheet_name_2024"
        assert parser.clean_column_name("  Trim  Me  ") == "trim_me"

    def test_parse_excel_standard(self, parser, temp_excel_file):
        result = parser.parse_file(temp_excel_file, sheet_name="Q1_Data")
        assert result["row_count"] == 4
        assert "revenue" in result["columns"]
        assert result["types"]["revenue"] == "numeric"
        assert result["data"][0]["month"] == "Jan"

    def test_parse_csv_standard(self, parser, temp_csv_file):
        result = parser.parse_file(temp_csv_file)
        assert result["row_count"] == 4
        assert "revenue" in result["columns"]
        assert result["data"][1]["revenue"] == 120000.0

    def test_parse_file_not_found(self, parser):
        with pytest.raises(FileNotFoundError):
            parser.parse_file("non_existent.xlsx")

    def test_parse_unsupported_extension(self, parser):
        with pytest.raises(ValueError, match="Unsupported file extension"):
            # Create a dummy file with unsupported extension
            with open("test.txt", "w") as f:
                f.write("test")
            try:
                parser.parse_file("test.txt")
            finally:
                if os.path.exists("test.txt"):
                    os.remove("test.txt")

    def test_parse_empty_file(self, parser):
        import polars as pl
        import tempfile
        with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
            pl.DataFrame().write_csv(tmp.name)
            tmp_path = tmp.name
        
        try:
            result = parser.parse_file(tmp_path)
            assert result["data"] == []
            assert result["row_count"] == 0
        finally:
            if os.path.exists(tmp_path):
                os.remove(tmp_path)
