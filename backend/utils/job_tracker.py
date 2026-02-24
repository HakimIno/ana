import uuid
from typing import Dict, Any, Optional
from models.response_models import JobStatus, JobStatusResponse
import logging

logger = logging.getLogger(__name__)

class JobTracker:
    """Simple in-memory store for tracking background jobs (Phase 2)."""
    
    _instance = None
    _jobs: Dict[str, Dict[str, Any]] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(JobTracker, cls).__new__(cls)
        return cls._instance

    def create_job(self) -> str:
        job_id = str(uuid.uuid4())
        self._jobs[job_id] = {
            "status": JobStatus.PENDING,
            "progress": 0,
            "message": "Job initialized",
            "result": None,
            "error": None
        }
        return job_id

    def update_job(self, job_id: str, status: Optional[JobStatus] = None, 
                   progress: Optional[int] = None, message: Optional[str] = None,
                   result: Optional[Dict[str, Any]] = None, error: Optional[str] = None):
        if job_id not in self._jobs:
            logger.warning(f"Attempted to update non-existent job {job_id}")
            return

        if status:
            self._jobs[job_id]["status"] = status
        if progress is not None:
            self._jobs[job_id]["progress"] = progress
        if message:
            self._jobs[job_id]["message"] = message
        if result:
            self._jobs[job_id]["result"] = result
        if error:
            self._jobs[job_id]["error"] = error

    def get_job(self, job_id: str) -> Optional[JobStatusResponse]:
        if job_id not in self._jobs:
            return None
        
        job_data = self._jobs[job_id]
        return JobStatusResponse(
            job_id=job_id,
            status=job_data["status"],
            progress=job_data["progress"],
            message=job_data["message"],
            result=job_data["result"],
            error=job_data["error"]
        )
