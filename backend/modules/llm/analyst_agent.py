from typing import List, Dict, Any, Optional
from openai import OpenAI
from modules.llm.prompts import ANALYST_SYSTEM_PROMPT, QUERY_PROMPT_TEMPLATE
from modules.analytics.financial_calculator import FinancialCalculator
from modules.rag.vector_store import VectorStore
from modules.rag.embedder import Embedder
from modules.rag.retriever import Retriever
from config import settings
import logging
import json
from models.response_models import AnalysisResponse
from modules.llm.output_parser import OutputParser

logger = logging.getLogger(__name__)

class AnalystAgent:
    """Main LLM orchestration for financial analysis."""

    def __init__(self, client: Optional[OpenAI] = None, retriever: Optional[Retriever] = None):
        self.client = client or OpenAI(api_key=settings.OPENAI_API_KEY)
        self.calculator = FinancialCalculator()
        
        # If retriever is not provided, initialize standard stack
        if retriever:
            self.retriever = retriever
        else:
            embedder = Embedder(client=self.client)
            vector_store = VectorStore()
            self.retriever = Retriever(embedder=embedder, vector_store=vector_store)

    def _prepare_metrics_context(self, data: List[Dict[str, Any]]) -> str:
        """Calculate summary metrics for the LLM context using Polars to prevent LLM math."""
        if not data:
            return "No numerical data available for metrics."
        
        import polars as pl
        df = pl.DataFrame(data)
        metrics = {}
        
        # Detect numeric columns and generate summary stats
        numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
        for col in numeric_cols:
            metrics[col] = self.calculator.summary_stats(df, col)
            
        return json.dumps(metrics, indent=2)

    def analyze(self, user_query: str, data_context: List[Dict[str, Any]] = None) -> AnalysisResponse:
        """
        Orchestrate the analysis by combining RAG, python math, and LLM interpretation.
        Returns a structured AnalysisResponse.
        """
        # 1. Get RAG context
        rag_context = self.retriever.get_context(user_query, top_k=5)

        # 2. Get calculated metrics
        metrics_context = self._prepare_metrics_context(data_context) if data_context else "No table data provided."

        # 3. Assemble prompt
        prompt = QUERY_PROMPT_TEMPLATE.format(
            calculated_metrics=metrics_context,
            rag_context=rag_context,
            user_question=user_query
        )

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            # 4. Parse and Validate
            return OutputParser.parse_analysis(
                response.choices[0].message.content, 
                rag_context=rag_context
            )
            
        except Exception as e:
            logger.error(f"LLM request/analysis failed: {e}")
            return AnalysisResponse(
                answer=f"Sorry, I encountered an error during analysis: {str(e)}",
                key_metrics={},
                recommendations=[],
                risks=[],
                confidence_score=0.0,
                status="error"
            )
