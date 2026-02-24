import json
import logging
from typing import Optional
from models.response_models import AnalysisResponse

logger = logging.getLogger(__name__)

class OutputParser:
    """Parses and validates LLM's raw JSON responses into AnalysisResponse."""

    @staticmethod
    def parse_analysis(raw_content: str, rag_context: Optional[str] = None) -> AnalysisResponse:
        """Parse raw JSON string into AnalysisResponse Pydantic model."""
        try:
            parsed_data = json.loads(raw_content)
            
            # Extract charts (new multi-chart schema)
            charts = parsed_data.get("charts", [])
            if not isinstance(charts, list):
                charts = []

            chart_data = parsed_data.get("chart_data", None)
            
            # Resiliency: If AI returns a dict instead of a list for chart_data
            if isinstance(chart_data, dict):
                # Try to extract the list from typical keys like 'data', 'values', or 'points'
                chart_data = chart_data.get("data") or chart_data.get("values") or chart_data.get("points") or None

            return AnalysisResponse(
                answer=parsed_data.get("answer", ""),
                thought=parsed_data.get("thought", None),
                key_metrics=parsed_data.get("key_metrics", {}),
                recommendations=parsed_data.get("recommendations", []),
                risks=parsed_data.get("risks", []),
                confidence_score=parsed_data.get("confidence_score", 0.0),
                charts=charts,
                chart_data=chart_data,
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
