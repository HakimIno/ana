from typing import Any, List, Dict
from modules.ingestion.excel_parser import ExcelParser
from modules.rag.chunker import Chunker
from modules.rag.embedder import Embedder
from modules.rag.vector_store import VectorStore
from utils.job_tracker import JobTracker
from models.response_models import JobStatus
import asyncio
import logging

logger = logging.getLogger(__name__)

async def process_batch(
    batch: List[Dict[str, Any]],
    batch_index: int,
    filename: str,
    embedder: Embedder,
    vector_store: VectorStore,
    semaphore: asyncio.Semaphore
):
    """Worker to process a single batch in parallel."""
    async with semaphore:
        batch_texts = [c["content"] for c in batch]
        
        # Run blocking network calls in threads to avoid blocking the event loop
        batch_embeddings = await asyncio.to_thread(embedder.get_embeddings, batch_texts)
        batch_sparse = await asyncio.to_thread(embedder.get_sparse_embeddings, batch_texts)
        batch_ids = [f"{filename}_{batch_index + j}" for j in range(len(batch))]
        
        # Add batch to vector store
        await asyncio.to_thread(
            vector_store.add_documents, 
            batch, 
            batch_embeddings, 
            batch_ids, 
            sparse_embeddings=batch_sparse
        )
        return len(batch)

async def process_file_async(
    job_id: str,
    file_path: str,
    filename: str,
    embedding_client: Any
):
    """
    Background task to process file with parallel batching and progress tracking.
    """
    tracker = JobTracker()
    parser = ExcelParser()
    chunker = Chunker()
    vector_store = VectorStore()
    embedder = Embedder(client=embedding_client)
    from modules.storage.metadata_manager import MetadataManager
    meta_manager = MetadataManager()
    
    try:
        tracker.update_job(job_id, status=JobStatus.PROCESSING, progress=5, message="Parsing file")
        
        # 1. Parse file (blocking call, but happens once)
        parsing_result = await asyncio.to_thread(parser.parse_file, file_path)
        tracker.update_job(job_id, progress=10, message=f"Parsed {parsing_result['row_count']} rows")
        
        # 1.5 Generate default metadata dictionary
        await asyncio.to_thread(
            meta_manager.generate_default_dictionary, 
            filename, 
            parsing_result["columns"]
        )
        
        # 2. Create chunks
        chunks = chunker.create_row_chunks(parsing_result)
        summary_chunk = chunker.create_summary_chunk(parsing_result)
        all_chunks = chunks + [summary_chunk]
        
        # Add filename to metadata for each chunk to allow filtering in Vector Store
        for chunk in all_chunks:
            if "metadata" not in chunk:
                chunk["metadata"] = {}
            chunk["metadata"]["filename"] = filename
        
        total_chunks = len(all_chunks)
        batch_size = 200 # Increased batch size for higher throughput
        max_concurrent_batches = 10 # Increase parallelism
        semaphore = asyncio.Semaphore(max_concurrent_batches)
        
        tracker.update_job(job_id, progress=15, message=f"Starting parallel embedding for {total_chunks} chunks")

        # 3. Create parallel tasks
        tasks = []
        for i in range(0, total_chunks, batch_size):
            batch = all_chunks[i : i + batch_size]
            tasks.append(process_batch(batch, i, filename, embedder, vector_store, semaphore))
        
        # 4. Execute and track progress
        processed_count = 0
        for future in asyncio.as_completed(tasks):
            count = await future
            processed_count += count
            progress = 15 + int((processed_count / total_chunks) * 85)
            # Update status less frequently for large datasets to avoid overhead
            if processed_count % (batch_size * 5) == 0 or processed_count == total_chunks:
                tracker.update_job(job_id, progress=progress, message=f"Indexed {processed_count}/{total_chunks} chunks")

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
