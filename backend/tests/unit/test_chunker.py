from modules.rag.chunker import Chunker

class TestChunker:
    """Tests for Chunker tabular-to-text conversion."""

    def test_create_row_chunks(self):
        chunker = Chunker()
        parsing_result = {
            "data": [
                {"month": "Jan", "revenue": 100},
                {"month": "Feb", "revenue": 120}
            ],
            "sheet_name": "Sales",
            "columns": ["month", "revenue"]
        }
        
        chunks = chunker.create_row_chunks(parsing_result)
        assert len(chunks) == 2
        assert "Sheet: Sales" in chunks[0]["content"]
        assert "month: Jan" in chunks[0]["content"]
        assert chunks[0]["metadata"]["month"] == "Jan"
        assert chunks[1]["metadata"]["row_index"] == 1

    def test_create_summary_chunk(self):
        chunker = Chunker()
        parsing_result = {
            "sheet_name": "Finance",
            "columns": ["rev", "cost"],
            "row_count": 10
        }
        
        chunk = chunker.create_summary_chunk(parsing_result)
        assert "sheet 'Finance'" in chunk["content"]
        assert "10 records" in chunk["content"]
        assert chunk["metadata"]["is_summary"] is True
