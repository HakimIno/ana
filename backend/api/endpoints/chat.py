from fastapi import APIRouter, Depends, HTTPException

import structlog
from api.deps import get_analyst_agent, get_llm_client_for_model
from modules.llm.factory import get_shared_retriever
from models.request_models import QueryRequest
from models.response_models import AnalysisResponse
from modules.llm.analyst_agent import AnalystAgent
from modules.storage.file_manager import FileManager
from modules.storage.metadata_manager import MetadataManager
from modules.ingestion.excel_parser import ExcelParser
from config import settings

logger = structlog.get_logger(__name__)
router = APIRouter()

def is_data_file(filename: str) -> bool:
    """Helper to check if a file is a valid data source."""
    ext = filename.lower().split('.')[-1]
    return ext in ['csv', 'xlsx', 'xls', 'parquet']

@router.post("/query", response_model=AnalysisResponse)
async def query_analyst(request: QueryRequest, agent: AnalystAgent = Depends(get_analyst_agent)):
    """Ask a natural language question about one or more files."""
    file_manager = FileManager()
    meta_manager = MetadataManager()
    try:
        data_context = []
        target_filenames = []
        
        # 1. Determine target files
        if request.group:
            all_files = file_manager.list_files()
            target_filenames = [
                f["filename"] for f in all_files 
                if meta_manager.get_group(f["filename"]) == request.group and is_data_file(f["filename"])
            ]
            if not target_filenames:
                raise HTTPException(status_code=404, detail=f"No files found for group: {request.group}")
        elif request.filenames:
            target_filenames = request.filenames
        elif request.filename:
            target_filenames = [request.filename]
        else:
            # Fallback to latest file
            all_files = file_manager.list_files()
            if all_files:
                data_files = [f for f in all_files if is_data_file(f["filename"])]
                if data_files:
                    # Broad Discovery: Ingest all data files for general context
                    target_filenames = [f["filename"] for f in data_files]

        # 2. Parse and combine data
        dfs = {}
        if target_filenames:
            parser = ExcelParser()
            for fname in target_filenames:
                f_path = file_manager.get_file_path(fname)
                # Just read the first few rows for context if it's large, 
                # but ExcelParser already returns full DFs for now.
                # DuckDB will handle the real SQL later.
                try:
                    df_obj = parser.parse_to_df(str(f_path))
                    
                    # Use clean name as key: e.g. "hotel_booking_2024.csv" -> "hotel_booking"
                    df_key = fname.lower().replace(".csv", "").replace(".xlsx", "").replace(".xls", "")
                    if "_" in df_key:
                        parts = df_key.split("_")
                        if len(parts) > 1:
                            df_key = "_".join(parts[:2])
                    
                    dfs[df_key] = df_obj
                except Exception as e:
                    logger.warning(f"Failed to parse context for {fname}: {e}")
            
            data_context = None # We will use dfs in the agent

        # 3. Choose agent and model
        if request.model and request.model != settings.OPENAI_MODEL:
            client, model_name = get_llm_client_for_model(request.model)
            shared_retriever = get_shared_retriever()
            active_agent = AnalystAgent(client=client, model_name=model_name, retriever=shared_retriever)
        else:
            active_agent = agent
            model_name = request.model

        return active_agent.analyze(
            request.question, 
            data_context=data_context, 
            session_id=request.session_id or "default",
            filename=", ".join(target_filenames) if target_filenames else "None",
            dfs=dfs if target_filenames else None,
            model_name=model_name,
        )
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/query/stream")
async def query_analyst_stream(request: QueryRequest, agent: AnalystAgent = Depends(get_analyst_agent)):
    """Stream AI analysis as Server-Sent Events."""
    from fastapi.responses import StreamingResponse

    file_manager = FileManager()
    meta_manager = MetadataManager()
    try:
        target_filenames = []

        if request.group:
            all_files = file_manager.list_files()
            target_filenames = [
                f["filename"] for f in all_files
                if meta_manager.get_group(f["filename"]) == request.group and is_data_file(f["filename"])
            ]
        elif request.filenames:
            target_filenames = request.filenames
        elif request.filename:
            target_filenames = [request.filename]
        else:
            all_files = file_manager.list_files()
            if all_files:
                # Broad Discovery: Ingest all data files for general context
                data_files = [f for f in all_files if is_data_file(f["filename"])]
                if data_files:
                    target_filenames = [f["filename"] for f in data_files]

        dfs = None
        data_context = None
        if target_filenames:
            dfs = {}
            parser = ExcelParser()
            for fname in target_filenames:
                try:
                    f_path = file_manager.get_file_path(fname)
                    df_obj = parser.parse_to_df(str(f_path))
                    df_key = fname.lower().replace(".csv", "").replace(".xlsx", "").replace(".xls", "")
                    if "_" in df_key:
                        parts = df_key.split("_")
                        if len(parts) > 1:
                            df_key = "_".join(parts[:2])
                    dfs[df_key] = df_obj
                except Exception as e:
                    logger.warning(f"Failed to parse context for {fname}: {e}")

        return StreamingResponse(
            _run_stream(request, agent, target_filenames, dfs, data_context),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )
    except Exception as e:
        logger.error(f"Stream query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))

async def _run_stream(request: QueryRequest, default_agent: AnalystAgent, target_filenames, dfs, data_context):
    """Choose agent (with correct model) and stream."""
    if request.model and request.model != settings.OPENAI_MODEL:
        client, model_name = get_llm_client_for_model(request.model)
        shared_retriever = get_shared_retriever()
        active_agent = AnalystAgent(client=client, model_name=model_name, retriever=shared_retriever)
    else:
        active_agent = default_agent

    async for event in active_agent.analyze_stream(
        request.question,
        data_context=data_context,
        session_id=request.session_id or "default",
        filename=", ".join(target_filenames) if target_filenames else "None",
        dfs=dfs,
    ):
        yield event

@router.get("/chat/history")
async def get_chat_history(session_id: str = "default", agent: AnalystAgent = Depends(get_analyst_agent)):
    """Retrieve chat history for a specific session."""
    try:
        history = agent.memory.get_history(session_id)
        return history
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/chat/sessions")
async def list_chat_sessions(agent: AnalystAgent = Depends(get_analyst_agent)):
    """List all available chat sessions."""
    try:
        return agent.memory.list_sessions()
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/chat/history")
async def clear_chat_history(session_id: str = "default", agent: AnalystAgent = Depends(get_analyst_agent)):
    """Clear chat history for a specific session."""
    try:
        agent.clear_history(session_id)
        return {"message": f"Chat history for session '{session_id}' cleared"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
