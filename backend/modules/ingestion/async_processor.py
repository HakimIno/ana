from typing import Any
from modules.ingestion.excel_parser import ExcelParser
from modules.rag.chunker import Chunker
from modules.rag.embedder import Embedder
from modules.rag.vector_store import VectorStore
from utils.job_tracker import JobTracker
from models.response_models import JobStatus
import logging
import asyncio

logger = logging.getLogger(__name__)

async def process_file_async(
    job_id: str,
    file_path: str,
    filename: str,
    embedding_client: Any
):
    """
    Background task to process file with batching and progress tracking.
    """
    tracker = JobTracker()
    parser = ExcelParser()
    chunker = Chunker()
    vector_store = VectorStore()
    embedder = Embedder(client=embedding_client)
    
    try:
        tracker.update_job(job_id, status=JobStatus.PROCESSING, progress=5, message="Parsing file")
        
        # 1. Parse file
        parsing_result = parser.parse_file(file_path)
        tracker.update_job(job_id, progress=10, message=f"Parsed {parsing_result['row_count']} rows")
        
        # 2. Create chunks
        chunks = chunker.create_row_chunks(parsing_result)
        summary_chunk = chunker.create_summary_chunk(parsing_result)
        all_chunks = chunks + [summary_chunk]
        
        total_chunks = len(all_chunks)
        batch_size = 50 # Phase 2: Batching
        
        processed_count = 0
        
        tracker.update_job(job_id, progress=15, message=f"Starting embedding for {total_chunks} chunks")

        # 3. Process Chunks in Batches
        for i in range(0, total_chunks, batch_size):
            batch = all_chunks[i : i + batch_size]
            batch_texts = [c["content"] for c in batch]
            
            # Generate embeddings for batch
            batch_embeddings = embedder.get_embeddings(batch_texts)
            batch_sparse = embedder.get_sparse_embeddings(batch_texts)
            batch_ids = [f"{filename}_{j}" for j in range(i, i + len(batch))]
            
            # Add batch to vector store
            vector_store.add_documents(batch, batch_embeddings, batch_ids, sparse_embeddings=batch_sparse)
            
            processed_count += len(batch)
            progress = 15 + int((processed_count / total_chunks) * 80)
            tracker.update_job(job_id, progress=progress, message=f"Indexed {processed_count}/{total_chunks} chunks")
            
            # Small sleep to prevent hammering AI API too hard and allow context switching
            await asyncio.sleep(0.1)

        tracker.update_job(
            job_id, 
            status=JobStatus.COMPLETED, 
            progress=100, 
            message="Upload and indexing complete",
            result={
                "filename": filename,
                "row_count": parsing_result["row_count"],
                "chunks_indexed": total_chunks
            }
        )
        logger.info(f"Job {job_id} successfully completed")

    except Exception as e:
        logger.error(f"Async processing failed for job {job_id}: {e}")
        tracker.update_job(
            job_id, 
            status=JobStatus.FAILED, 
            error=str(e), 
            message="Processing failed"
        )
