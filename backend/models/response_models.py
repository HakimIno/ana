from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from enum import Enum

class JobStatus(str, Enum):
    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"

class JobStatusResponse(BaseModel):
    """Status of a background job."""
    job_id: str
    status: JobStatus
    progress: int # 0-100
    message: str
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

class ChartConfig(BaseModel):
    """Configuration for a single chart."""
    type: str = "area" # area, bar, line, pie, radar
    title: str
    data: List[Dict[str, Any]]

class TokenUsage(BaseModel):
    """Token usage for LLM requests."""
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

class AnalysisResponse(BaseModel):
    """Structured response for financial analysis."""
    answer: str
    thought: Optional[str] = None
    python_code: Optional[str] = None
    token_usage: Optional[TokenUsage] = None
    key_metrics: Dict[str, Any]
    recommendations: List[str]
    risks: List[str]
    confidence_score: float
    charts: Optional[List[ChartConfig]] = []
    table_data: Optional[Dict[str, Any]] = None
    chart_data: Optional[List[Dict[str, Any]]] = None # Legacy
    source_documents: Optional[List[str]] = []
    generated_file: Optional[str] = None # URL or path to generated PDF
    status: str = "success"

class FileInfo(BaseModel):
    """Information about a stored file."""
    filename: str
    size: int
    created_at: float
    group: Optional[str] = None
