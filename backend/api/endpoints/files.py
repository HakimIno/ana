from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from typing import List, Dict, Any
import structlog
from api.deps import get_embedding_client
from models.response_models import FileInfo, JobStatusResponse
from modules.ingestion.async_processor import process_file_async
from modules.storage.file_manager import FileManager
from modules.storage.metadata_manager import MetadataManager
from modules.storage.df_cache import DataFrameCache
from modules.rag.vector_store import VectorStore
from utils.job_tracker import JobTracker

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/upload", response_model=Dict[str, str])
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    client: Any = Depends(get_embedding_client)
):
    """Upload a file and start asynchronous indexing."""
    file_manager = FileManager()
    tracker = JobTracker()
    
    # 1. Save file
    content = await file.read()
    try:
        file_path = file_manager.save_file(content, file.filename)
        
        # 2. Create Job ID
        job_id = tracker.create_job()
        
        # 3. Start background processing
        background_tasks.add_task(
            process_file_async, 
            job_id, 
            str(file_path), 
            file.filename, 
            client
        )
        
        return {"job_id": job_id, "message": "File upload accepted and processing started"}
        
    except Exception as e:
        logger.error(f"Upload initialization failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/upload/status/{job_id}", response_model=JobStatusResponse)
async def get_upload_status(job_id: str):
    """Get the status of a background indexing job."""
    tracker = JobTracker()
    status = tracker.get_job(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@router.get("/files", response_model=List[FileInfo])
async def list_files():
    """List all uploaded files with group tags."""
    file_manager = FileManager()
    meta_manager = MetadataManager()
    files = file_manager.list_files()
    
    # Inject group info for each file
    for f in files:
        f["group"] = meta_manager.get_group(f["filename"])
        
    return files

@router.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a specific file and reset the vector store."""
    file_manager = FileManager()
    vector_store = VectorStore()
    
    deleted = file_manager.delete_file(filename)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    
    # Invalidate cache for this file
    DataFrameCache().invalidate(filename)
    
    # Reset vector store
    vector_store.reset()
    return {"message": f"File '{filename}' deleted and index reset"}

@router.patch("/files/{filename}")
async def update_file_group(filename: str, group: str):
    """Assign or update a category/group for a specific file."""
    meta_manager = MetadataManager()
    meta_manager.save_group(filename, group)
    return {"message": f"File '{filename}' assigned to group '{group}'"}

@router.delete("/files")
async def clear_storage():
    """Clear all files and reset vector store."""
    file_manager = FileManager()
    vector_store = VectorStore()
    file_manager.cleanup()
    vector_store.reset()
    DataFrameCache().clear()
    return {"message": "Storage and index cleared"}

@router.post("/files/sync")
async def sync_files(background_tasks: BackgroundTasks, client: Any = Depends(get_embedding_client)):
    """Sync all files in uploads with the vector store."""
    file_manager = FileManager()
    tracker = JobTracker()
    files = file_manager.list_files()
    
    results = []
    for f in files:
        job_id = tracker.create_job()
        background_tasks.add_task(
            process_file_async, 
            job_id, 
            f["path"], 
            f["filename"], 
            client
        )
        results.append({"filename": f["filename"], "job_id": job_id})
    
    return {"message": "Sync jobs started", "jobs": results}
