import json
import ast
import re
import logging
from typing import Optional, Any
from models.response_models import AnalysisResponse

logger = logging.getLogger(__name__)

class OutputParser:
    """Parses and validates LLM's raw JSON responses into AnalysisResponse."""

    @staticmethod
    def clean_json(raw_content: str) -> str:
        """Extract JSON string from potentially markdown-wrapped text."""
        if not raw_content:
            return "{}"
        cleaned = raw_content.strip()
        
        # Strip markdown code fences
        if cleaned.startswith("```"):
            match = re.search(r'```(?:json)?(.*?)```', cleaned, re.DOTALL | re.IGNORECASE)
            if match:
                cleaned = match.group(1).strip()
        
        # Extract JSON object
        if "{" in cleaned and "}" in cleaned:
            start = cleaned.find("{")
            end = cleaned.rfind("}")
            if start != -1 and end != -1 and start < end:
                cleaned = cleaned[start:end+1]
        
        # Try parsing as-is first
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass
        
        # Fix common LLM JSON issues:
        # 1. Remove trailing commas before } or ]
        cleaned = re.sub(r',\s*([}\]])', r'\1', cleaned)
        
        # 2. Try again after trailing comma fix
        try:
            json.loads(cleaned)
            return cleaned
        except json.JSONDecodeError:
            pass
        
        # 3. Try using ast.literal_eval (handles single quotes, True/False/None)
        try:
            parsed = ast.literal_eval(cleaned)
            return json.dumps(parsed, ensure_ascii=False)
        except (ValueError, SyntaxError):
            pass
        
        # 4. Attempt to fix single quotes by replacing them
        # Replace single-quoted keys/values with double-quoted ones
        # This is a best-effort heuristic
        try:
            fixed = cleaned.replace("'", '"')
            # Fix Python True/False/None → JSON true/false/null
            fixed = re.sub(r'\bTrue\b', 'true', fixed)
            fixed = re.sub(r'\bFalse\b', 'false', fixed)
            fixed = re.sub(r'\bNone\b', 'null', fixed)
            json.loads(fixed)
            return fixed
        except json.JSONDecodeError:
            pass
        
        # Return best effort
        return cleaned

    @staticmethod
    def parse_analysis(raw_content: str, rag_context: Optional[str] = None, token_usage: Optional[Any] = None) -> AnalysisResponse:
        """Parse raw JSON string into AnalysisResponse Pydantic model."""
        try:
            cleaned_content = OutputParser.clean_json(raw_content)
            try:
                parsed_data = json.loads(cleaned_content)
            except json.JSONDecodeError as e:
                logger.error(f"JSON Decode Error in OutputParser. Raw content:\n{raw_content}\nCleaned content:\n{cleaned_content}")
                raise e
            
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

            # Validate recommendations and risks are lists of strings
            def _stringify_list(items):
                if not isinstance(items, list):
                    return []
                return [
                    v if isinstance(v, str) else json.dumps(v, ensure_ascii=False)
                    for v in items
                ]
            
            recommendations = _stringify_list(parsed_data.get("recommendations", []))
            risks = _stringify_list(parsed_data.get("risks", []))

            return AnalysisResponse(
                answer=parsed_data.get("answer", ""),
                thought=parsed_data.get("thought", None),
                python_code=parsed_data.get("python_code", None),
                token_usage=token_usage,
                key_metrics=parsed_data.get("key_metrics", {}),
                recommendations=recommendations,
                risks=risks,
                confidence_score=parsed_data.get("confidence_score", 0.0),
                charts=charts,
                table_data=parsed_data.get("table_data", None),
                chart_data=None,  # Deprecated: always use charts
                source_documents=[rag_context] if rag_context else [],
                generated_file=parsed_data.get("generated_file", None)
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
