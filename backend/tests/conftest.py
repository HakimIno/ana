import pytest
import polars as pl
import os
import tempfile
from modules.analytics.financial_calculator import FinancialCalculator
from modules.ingestion.excel_parser import ExcelParser

@pytest.fixture
def calculator():
    return FinancialCalculator()

@pytest.fixture
def parser():
    return ExcelParser()

@pytest.fixture
def sample_financial_df():
    """Standard test dataset for calculations using Polars."""
    data = {
        "Month": ["Jan", "Feb", "Mar", "Apr"],
        "Revenue": [100000.0, 120000.0, 95000.0, 140000.0],
        "Cost": [70000.0, 80000.0, 75000.0, 90000.0],
        "Expenses": [15000.0, 18000.0, 15000.0, 20000.0]
    }
    return pl.DataFrame(data)

@pytest.fixture
def temp_excel_file(sample_financial_df):
    """Creates a temporary Excel file for testing using Polars."""
    with tempfile.NamedTemporaryFile(suffix=".xlsx", delete=False) as tmp:
        # Polars write_excel requires 'xlsxwriter' or 'openpyxl'
        sample_financial_df.write_excel(tmp.name, worksheet="Q1_Data")
        tmp_path = tmp.name
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)

@pytest.fixture
def temp_csv_file(sample_financial_df):
    """Creates a temporary CSV file for testing using Polars."""
    with tempfile.NamedTemporaryFile(suffix=".csv", delete=False) as tmp:
        sample_financial_df.write_csv(tmp.name)
        tmp_path = tmp.name
    
    yield tmp_path
    
    if os.path.exists(tmp_path):
        os.remove(tmp_path)
