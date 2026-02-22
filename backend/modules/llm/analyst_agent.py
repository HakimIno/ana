from typing import List, Dict, Any
from openai import OpenAI
from modules.llm.prompts import ANALYST_SYSTEM_PROMPT, QUERY_PROMPT_TEMPLATE
from modules.analytics.financial_calculator import FinancialCalculator
from modules.rag.vector_store import VectorStore
from modules.rag.embedder import Embedder
from config import settings
import logging
import json

logger = logging.getLogger(__name__)

class AnalystAgent:
    """Main LLM orchestration for financial analysis."""

    def __init__(self):
        api_key = settings.OPENAI_API_KEY or "missing-key"
        self.client = OpenAI(api_key=api_key)
        self.calculator = FinancialCalculator()
        self.vector_store = VectorStore()
        self.embedder = Embedder()

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

    def analyze(self, user_query: str, data_context: List[Dict[str, Any]] = None) -> str:
        """
        Orchestrate the analysis by combining RAG, python math, and LLM interpretation.
        """
        # 1. Get RAG context
        try:
            query_embedding = self.embedder.get_embedding(user_query)
            rag_results = self.vector_store.query(query_embedding, n_results=5)
            rag_context = "\n".join(rag_results["documents"][0])
        except Exception as e:
            logger.warning(f"RAG lookup failed: {e}")
            rag_context = "Could not retrieve document context."

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
                model="gpt-4o", # Using a strong reasoning model
                messages=[
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.2 # Lower temperature for analytical consistency
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"Sorry, I encountered an error while analyzing the data: {str(e)}"
