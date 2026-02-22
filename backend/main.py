from fastapi import FastAPI, UploadFile, File, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from typing import List
from config import settings
from models.request_models import QueryRequest, FileUploadResponse
from models.response_models import AnalysisResponse, FileInfo
from modules.ingestion.excel_parser import ExcelParser
from modules.storage.file_manager import FileManager
from modules.rag.chunker import Chunker
from modules.rag.embedder import Embedder
from modules.rag.vector_store import VectorStore
from modules.llm.analyst_agent import AnalystAgent

app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Backend API for AI Business Analyst Assistant"
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
def get_analyst_agent():
    return AnalystAgent()

@app.get("/")
async def root():
    return {"message": f"Welcome to {settings.PROJECT_NAME}", "version": settings.VERSION}

@app.post("/upload", response_model=FileUploadResponse)
async def upload_file(file: UploadFile = File(...)):
    """Upload a file, parse it, and index it for RAG."""
    parser = ExcelParser()
    file_manager = FileManager()
    chunker = Chunker()
    vector_store = VectorStore()
    # 1. Save file
    content = await file.read()
    try:
        file_path = file_manager.save_file(content, file.filename)
        
        # 2. Parse file
        parsing_result = parser.parse_file(str(file_path))
        
        # 3. Create chunks
        chunks = chunker.create_row_chunks(parsing_result)
        summary_chunk = chunker.create_summary_chunk(parsing_result)
        all_chunks = chunks + [summary_chunk]
        
        # 4. Generate embeddings and store
        embedder = Embedder()
        texts = [c["content"] for c in all_chunks]
        embeddings = embedder.get_embeddings(texts)
        ids = [f"{file.filename}_{i}" for i in range(len(all_chunks))]
        
        vector_store.add_documents(all_chunks, embeddings, ids)
        
        return FileUploadResponse(
            filename=file.filename,
            row_count=parsing_result["row_count"],
            sheet_name=parsing_result["sheet_name"],
            columns=parsing_result["columns"],
            message="File uploaded and indexed successfully"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/query", response_model=AnalysisResponse)
async def query_analyst(request: QueryRequest, agent: AnalystAgent = Depends(get_analyst_agent)):
    """Ask a natural language question about the uploaded data."""
    file_manager = FileManager()
    parser = ExcelParser()
    try:
        latest_files = file_manager.list_files()
        data_context = []
        if latest_files:
            latest_file = sorted(latest_files, key=lambda x: x["created_at"], reverse=True)[0]
            parsing_result = parser.parse_file(latest_file["path"])
            data_context = parsing_result["data"]

        answer = agent.analyze(request.question, data_context=data_context)
        return AnalysisResponse(answer=answer)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

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
