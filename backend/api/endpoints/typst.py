from fastapi import APIRouter, File, UploadFile, HTTPException
import structlog
from typing import Dict, Any

logger = structlog.get_logger(__name__)
router = APIRouter()

@router.post("/generate", response_model=Dict[str, Any])
async def generate_typst_from_pdf(
    file: UploadFile = File(...)
):
    """
    Receive a PDF file and start the AI process to convert it to Typst code.
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Only PDF files are supported.")
        
    try:
        content = await file.read()
        
        # Process PDF with PyMuPDF
        from modules.typst_gen.pdf_parser import parse_pdf_for_ai
        from modules.typst_gen.generator import generate_typst
        
        pages = parse_pdf_for_ai(content)
        num_pages = len(pages)
        
        # Call LLM Generator
        raw_typst = await generate_typst(pages)
        
        return {
            "status": "success",
            "message": f"Successfully received PDF with {num_pages} pages.",
            "raw_typst": raw_typst
        }
    except Exception as e:
        logger.error(f"Typst generation failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))
