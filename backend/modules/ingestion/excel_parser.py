import polars as pl
from typing import List, Dict, Any, Optional
from pathlib import Path
import logging
import os

logger = logging.getLogger(__name__)

class ExcelParser:
    """Parser for Excel and CSV files with data cleaning and type detection using Polars."""

    def __init__(self):
        self.supported_extensions = {".xlsx", ".xls", ".csv"}

    def get_sheet_names(self, file_path: str) -> List[str]:
        """Detect sheet names in an Excel file."""
        ext = Path(file_path).suffix.lower()
        if ext == ".csv":
            return ["default"]
        
        try:
            # Using fastexcel directly to get sheet names
            import fastexcel
            wb = fastexcel.read_excel(file_path)
            return wb.sheet_names
        except Exception as e:
            logger.error(f"Error reading sheet names from {file_path}: {e}")
            raise ValueError(f"Could not read Excel file: {e}")

    def clean_column_name(self, name: str) -> str:
        """Clean column names to be lowercase and underscore-separated."""
        import re
        # Remove special characters and replace spaces with underscores
        clean = re.sub(r'[^a-zA-Z0-9\s]', '', str(name))
        clean = re.sub(r'\s+', '_', clean.strip().lower())
        return clean

    def parse_file(self, file_path: str, sheet_name: Optional[str] = None) -> Dict[str, Any]:
        """
        Parse Excel/CSV file, clean columns, and detect data types using Polars.
        
        Returns:
            Dict containing cleaned data, columns, and detected types.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        ext = Path(file_path).suffix.lower()
        if ext not in self.supported_extensions:
            raise ValueError(f"Unsupported file extension: {ext}")

        try:
            if ext == ".csv":
                try:
                    df = pl.read_csv(file_path)
                except Exception as e:
                    # Handle empty files or other CSV errors
                    if "empty" in str(e).lower():
                        return {"data": [], "columns": [], "types": {}, "row_count": 0, "sheet_name": sheet_name or "default"}
                    raise e
            else:
                # Use calamine engine for speed and reliability
                df = pl.read_excel(file_path, sheet_name=sheet_name or "Sheet1", engine="calamine")

            if df.is_empty():
                return {"data": [], "columns": [], "types": {}, "row_count": 0, "sheet_name": sheet_name or "default"}

            # Clean column names
            original_columns = df.columns
            cleaned_columns = [self.clean_column_name(col) for col in original_columns]
            
            # Rename columns in Polars
            rename_map = dict(zip(original_columns, cleaned_columns))
            df = df.rename(rename_map)

            # Detect data types
            types = {}
            for col in df.columns:
                dtype = df.schema[col]
                if dtype.is_numeric():
                    types[col] = "numeric"
                elif dtype.is_temporal():
                    types[col] = "datetime"
                else:
                    # Try to convert to datetime if it's a string
                    if dtype == pl.Utf8:
                        try:
                            # Try a few common formats or let Polars guess
                            # In Polars we can use try_parse_datetime or similar logic
                            temp_col = df[col].str.to_datetime(strict=False)
                            if temp_col.null_count() < len(df) * 0.2: # If less than 20% are null after conversion
                                types[col] = "datetime"
                                continue
                        except Exception:
                            pass
                    types[col] = "string"

            # Convert to list of dicts for JSON compatibility (Polars outputs None for nulls by default)
            data = df.to_dicts()
            
            return {
                "data": data,
                "columns": cleaned_columns,
                "types": types,
                "row_count": len(df),
                "sheet_name": sheet_name or "default"
            }

        except Exception as e:
            logger.error(f"Error parsing file {file_path}: {e}")
            raise ValueError(f"Failed to parse file: {e}")
