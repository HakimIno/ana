from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AnalysisResponse(BaseModel):
    """Response model for analysis results."""
    answer: str
    source_documents: Optional[List[str]] = []
    calculated_metrics: Optional[Dict[str, Any]] = {}
    status: str = "success"

class FileInfo(BaseModel):
    """Information about a stored file."""
    filename: str
    size: int
    created_at: float
