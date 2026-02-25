from pydantic import BaseModel
from typing import Optional, List, Dict, Any

class QueryRequest(BaseModel):
    """Request model for natural language queries."""
    question: str
    session_id: Optional[str] = "default"
    filename: Optional[str] = None
    filenames: Optional[List[str]] = None
    group: Optional[str] = None
    # Optional parameters for advanced filtering
    filters: Optional[Dict[str, Any]] = None

class FileUploadResponse(BaseModel):
    """Response model for file upload and indexing."""
    filename: str
    row_count: int
    sheet_name: str
    columns: List[str]
    message: str
