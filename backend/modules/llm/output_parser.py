import json
import logging
from typing import Optional, Any
from models.response_models import AnalysisResponse

logger = logging.getLogger(__name__)

class OutputParser:
    """Parses and validates LLM's raw JSON responses into AnalysisResponse."""

    @staticmethod
    def parse_analysis(raw_content: str, rag_context: Optional[str] = None, token_usage: Optional[Any] = None) -> AnalysisResponse:
        """Parse raw JSON string into AnalysisResponse Pydantic model."""
        try:
            parsed_data = json.loads(raw_content)
            
            # Extract charts (unified schema)
            charts = parsed_data.get("charts", [])
            if not isinstance(charts, list):
                charts = []

            # Merge legacy chart_data into charts if present
            legacy_chart_data = parsed_data.get("chart_data", None)
            if isinstance(legacy_chart_data, dict):
                legacy_chart_data = legacy_chart_data.get("data") or legacy_chart_data.get("values") or None
            if legacy_chart_data and isinstance(legacy_chart_data, list) and not charts:
                charts = [{"type": "bar", "title": parsed_data.get("title", "Chart"), "data": legacy_chart_data}]

            logger.info(f"OutputParser: parsed {len(charts)} chart(s) from response")

            return AnalysisResponse(
                answer=parsed_data.get("answer", ""),
                thought=parsed_data.get("thought", None),
                python_code=parsed_data.get("python_code", None),
                token_usage=token_usage,
                key_metrics=parsed_data.get("key_metrics", {}),
                recommendations=parsed_data.get("recommendations", []),
                risks=parsed_data.get("risks", []),
                confidence_score=parsed_data.get("confidence_score", 0.0),
                charts=charts,
                table_data=parsed_data.get("table_data", None),
                chart_data=None,  # Deprecated: always use charts
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
