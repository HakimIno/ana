from typing import List, Dict, Any

class Chunker:
    """Utility to convert tabular data into descriptive text chunks for RAG."""

    def create_row_chunks(self, parsing_result: Dict[str, Any], rows_per_chunk: int = 10) -> List[Dict[str, Any]]:
        """
        Convert row-based data into descriptive text chunks, grouping multiple rows 
        into a single chunk for better performance and context.
        """
        data = parsing_result.get("data", [])
        sheet_name = parsing_result.get("sheet_name", "default")
        chunks = []

        for i in range(0, len(data), rows_per_chunk):
            batch = data[i : i + rows_per_chunk]
            
            # Combine multiple rows into one descriptive text
            batch_lines = []
            for j, row in enumerate(batch):
                row_items = [f"{col}: {val}" for col, val in row.items() if val is not None]
                row_text = f"[Row {i + j + 1}]: " + ", ".join(row_items)
                batch_lines.append(row_text)
            
            content = f"Sheet: {sheet_name} | Group {i//rows_per_chunk + 1} | \n" + "\n".join(batch_lines)
            
            # Collect metadata from all rows in the batch (deduplicated)
            # For simplicity, we use the first row's key attributes if they represent categories
            chunks.append({
                "content": content,
                "metadata": {
                    "source": sheet_name,
                    "start_row": i,
                    "end_row": i + len(batch) - 1,
                    "is_grouped": True
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
