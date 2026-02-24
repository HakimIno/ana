from fastapi import FastAPI, UploadFile, File, HTTPException, Depends, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from openai import OpenAI
from typing import List, Any, Dict, Optional
import logging
from config import settings
from models.request_models import QueryRequest
from models.response_models import AnalysisResponse, FileInfo, JobStatusResponse
from modules.ingestion.excel_parser import ExcelParser
from modules.ingestion.async_processor import process_file_async
from modules.storage.file_manager import FileManager
from modules.rag.vector_store import VectorStore
from modules.llm.analyst_agent import AnalystAgent
from utils.job_tracker import JobTracker
from contextlib import asynccontextmanager

logger = logging.getLogger(__name__)

# Global agent instance
_analyst_agent: Optional[AnalystAgent] = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    global _analyst_agent
    logger.info("Starting up backend...")
    
    # Pre-initialize AnalystAgent (loads models, connects to DB)
    client = get_llm_client()
    _analyst_agent = AnalystAgent(client=client)
    
    yield
    # Shutdown
    logger.info("Shutting down backend...")
    VectorStore.clear_client()

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AI Business Analyst Assistant",
    lifespan=lifespan
)

# CORS Configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In production, restrict this
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Helper for dependency injection
def get_llm_client():
    """Client for Chat/Analysis (Z.AI requested)."""
    if settings.CHAT_PROVIDER == "zai":
        from zai import ZaiClient
        return ZaiClient(api_key=settings.ZAI_API_KEY)
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def get_embedding_client():
    """Client for Embeddings (OpenAI requested)."""
    if settings.EMBEDDING_PROVIDER == "zai":
        from zai import ZaiClient
        return ZaiClient(api_key=settings.ZAI_API_KEY)
    return OpenAI(api_key=settings.OPENAI_API_KEY)

def get_analyst_agent():
    if _analyst_agent is None:
        # Fallback in case lifespan wasn't triggered (e.g. some tests)
        client = get_llm_client()
        return AnalystAgent(client=client)
    return _analyst_agent

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}", "version": settings.VERSION}

@app.post("/upload", response_model=Dict[str, str])
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

@app.get("/upload/status/{job_id}", response_model=JobStatusResponse)
async def get_upload_status(job_id: str):
    """Get the status of a background indexing job."""
    tracker = JobTracker()
    status = tracker.get_job(job_id)
    if not status:
        raise HTTPException(status_code=404, detail="Job not found")
    return status

@app.post("/query", response_model=AnalysisResponse)
async def query_analyst(request: QueryRequest, agent: AnalystAgent = Depends(get_analyst_agent)):
    """Ask a natural language question about the uploaded data."""
    file_manager = FileManager()
    parser = ExcelParser()
    try:
        latest_files = file_manager.list_files()
        data_context = []
        if latest_files:
            # Choose specific file if requested, else latest
            if request.filename:
                target_file = next((f for f in latest_files if f["filename"] == request.filename), None)
                if not target_file:
                    raise HTTPException(status_code=404, detail=f"File {request.filename} not found")
            else:
                target_file = sorted(latest_files, key=lambda x: x["created_at"], reverse=True)[0]
            
            parsing_result = parser.parse_file(target_file["path"])
            data_context = parsing_result["data"]

        return agent.analyze(
            request.question, 
            data_context=data_context, 
            session_id=request.session_id or "default",
            filename=request.filename
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/history")
async def get_chat_history(session_id: str = "default", agent: AnalystAgent = Depends(get_analyst_agent)):
    """Retrieve chat history for a specific session."""
    try:
        history = agent.memory.get_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/chat/sessions")
async def list_chat_sessions(agent: AnalystAgent = Depends(get_analyst_agent)):
    """List all available chat sessions."""
    try:
        return agent.memory.list_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/chat/history")
async def clear_chat_history(session_id: str = "default", agent: AnalystAgent = Depends(get_analyst_agent)):
    """Clear chat history for a specific session."""
    try:
        agent.clear_history(session_id)
        return {"message": f"Chat history for session '{session_id}' cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/files/{filename}")
async def delete_file(filename: str):
    """Delete a specific file and reset the vector store."""
    file_manager = FileManager()
    vector_store = VectorStore()
    
    deleted = file_manager.delete_file(filename)
    if not deleted:
        raise HTTPException(status_code=404, detail=f"File {filename} not found")
    
    # Reset vector store to ensure consistency (targeted deletion could be complex)
    vector_store.reset()
    return {"message": f"File '{filename}' deleted and index reset"}

@app.get("/files", response_model=List[FileInfo])
async def list_files():
    """List all uploaded files."""
    file_manager = FileManager()
    return file_manager.list_files()

@app.delete("/files")
async def clear_storage():
    """Clear all files and reset vector store."""
    file_manager = FileManager()
    vector_store = VectorStore()
    file_manager.cleanup()
    vector_store.reset()
    return {"message": "Storage and index cleared"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
