from typing import List, Dict, Any
import json

class Chunker:
    """Utility to convert tabular data into descriptive text chunks for RAG."""

    def create_row_chunks(self, parsing_result: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Convert row-based data into descriptive text chunks.
        
        Each chunk contains the text representation of the row and associated metadata.
        """
        data = parsing_result.get("data", [])
        sheet_name = parsing_result.get("sheet_name", "default")
        chunks = []

        for i, row in enumerate(data):
            # Create a descriptive string for the row
            # Example: "In January, the revenue was 100,000, cost was 70,000..."
            row_items = []
            for col, val in row.items():
                if val is not None:
                    row_items.append(f"{col}: {val}")
            
            content = f"Sheet: {sheet_name} | Data Point {i+1}: " + ", ".join(row_items)
            
            chunks.append({
                "content": content,
                "metadata": {
                    "source": sheet_name,
                    "row_index": i,
                    **{k: str(v) for k, v in row.items() if v is not None} # Metadata for filtering
                }
            })

        return chunks

    def create_summary_chunk(self, parsing_result: Dict[str, Any]) -> Dict[str, Any]:
        """Create a summary chunk for the entire dataset/sheet."""
        sheet_name = parsing_result.get("sheet_name", "default")
        columns = parsing_result.get("columns", [])
        row_count = parsing_result.get("row_count", 0)

        content = f"This dataset is from sheet '{sheet_name}'. It contains {row_count} records with columns: {', '.join(columns)}."
        
        return {
            "content": content,
            "metadata": {
                "source": sheet_name,
                "is_summary": True,
                "columns": columns,
                "row_count": row_count
            }
        }
