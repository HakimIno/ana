import json
import logging
from typing import Any, Dict, Optional
from models.response_models import AnalysisResponse

logger = logging.getLogger(__name__)

class OutputParser:
    """Parses and validates LLM's raw JSON responses into AnalysisResponse."""

    @staticmethod
    def parse_analysis(raw_content: str, rag_context: Optional[str] = None) -> AnalysisResponse:
        """Parse raw JSON string into AnalysisResponse Pydantic model."""
        try:
            parsed_data = json.loads(raw_content)
            
            return AnalysisResponse(
                answer=parsed_data.get("answer", ""),
                key_metrics=parsed_data.get("key_metrics", {}),
                recommendations=parsed_data.get("recommendations", []),
                risks=parsed_data.get("risks", []),
                confidence_score=parsed_data.get("confidence_score", 0.0),
                source_documents=[rag_context] if rag_context else []
            )
        except json.JSONDecodeError as e:
            logger.error(f"JSON Parsing failed: {e}")
            return AnalysisResponse(
                answer="Failed to parse analysis results. The AI returned malformed data.",
                key_metrics={},
                recommendations=[],
                risks=[],
                confidence_score=0.0,
                status="error"
            )
        except Exception as e:
            logger.error(f"Output parsing error: {e}")
            return AnalysisResponse(
                answer=f"An unexpected error occurred during result parsing: {str(e)}",
                key_metrics={},
                recommendations=[],
                risks=[],
                confidence_score=0.0,
                status="error"
            )
