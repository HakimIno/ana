from pydantic import BaseModel
from typing import List, Dict, Any, Optional

class AnalysisResponse(BaseModel):
    """Structured response for financial analysis."""
    answer: str
    key_metrics: Dict[str, Any]
    recommendations: List[str]
    risks: List[str]
    confidence_score: float
    source_documents: Optional[List[str]] = []
    status: str = "success"

class FileInfo(BaseModel):
    """Information about a stored file."""
    filename: str
    size: int
    created_at: float
