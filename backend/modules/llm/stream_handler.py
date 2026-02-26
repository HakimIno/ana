"""SSE streaming handler for real-time AI responses."""
import json
import structlog
from typing import AsyncGenerator, Dict, Any, Optional

from models.response_models import TokenUsage
from modules.llm.output_parser import OutputParser

logger = structlog.get_logger(__name__)


class StreamHandler:
    """Handles streaming LLM responses via Server-Sent Events (SSE)."""

    @staticmethod
    def _sse_event(event_type: str, data: Any) -> str:
        """Format a single SSE event."""
        payload = json.dumps({"type": event_type, "data": data}, ensure_ascii=False)
        return f"data: {payload}\n\n"

    @staticmethod
    async def stream_analysis(
        client,
        model_name: str,
        create_params: Dict,
        total_usage: TokenUsage,
        python_code: Optional[str] = None,
        exec_result: Optional[Dict] = None,
        rag_context: Optional[str] = None,
    ) -> AsyncGenerator[str, None]:
        """
        Stream the LLM response as SSE events.
        
        Event types:
        - thinking: The AI's thought process
        - token: A streamed answer token
        - code: Python code for execution
        - metrics: Key metrics
        - done: Final complete response JSON
        - error: Error message
        """
        try:
            # If we have exec_result, this is Turn 2 (refinement)
            if exec_result is not None:
                yield StreamHandler._sse_event("status", "Synthesizing results...")
            else:
                yield StreamHandler._sse_event("status", "Analyzing data...")

            # Use streaming API
            stream_params = {**create_params, "stream": True}
            stream = client.chat.completions.create(**stream_params)

            accumulated = ""
            for chunk in stream:
                if not chunk.choices:
                    continue
                delta = chunk.choices[0].delta
                if delta and delta.content:
                    accumulated += delta.content
                    yield StreamHandler._sse_event("token", delta.content)

            # Track usage from final chunk if available
            if hasattr(chunk, "usage") and chunk.usage:
                total_usage.prompt_tokens += chunk.usage.prompt_tokens
                total_usage.completion_tokens += chunk.usage.completion_tokens
                total_usage.total_tokens += chunk.usage.total_tokens

            # Parse the accumulated response
            try:
                parsed_data = json.loads(accumulated)
                
                # Send structured parts
                if parsed_data.get("thought"):
                    yield StreamHandler._sse_event("thinking", parsed_data["thought"])
                if parsed_data.get("python_code") and not exec_result:
                    yield StreamHandler._sse_event("code", parsed_data["python_code"])
                if parsed_data.get("key_metrics"):
                    yield StreamHandler._sse_event("metrics", parsed_data["key_metrics"])

            except json.JSONDecodeError:
                parsed_data = {"answer": accumulated}

            # Build final response
            final_response = OutputParser.parse_analysis(
                accumulated, rag_context=rag_context, token_usage=total_usage
            )
            if python_code:
                final_response.python_code = python_code

            yield StreamHandler._sse_event("done", final_response.model_dump())

        except Exception as e:
            logger.error("stream_error", error=str(e))
            yield StreamHandler._sse_event("error", str(e))
