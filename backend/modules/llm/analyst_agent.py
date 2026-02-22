from typing import List, Dict, Any
from openai import OpenAI
from zai import ZaiClient
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

    def __init__(self, client=None, retriever: Retriever = None):
        """Initialize the AnalystAgent with a client and retriever."""
        if client:
            self.client = client
        else:
            if settings.CHAT_PROVIDER == "zai":
                logger.info(f"Using Z.AI provider with model {settings.GLM_MODEL}")
                self.client = ZaiClient(api_key=settings.ZAI_API_KEY)
            else:
                logger.info(f"Using OpenAI provider with model {settings.OPENAI_MODEL}")
                self.client = OpenAI(api_key=settings.OPENAI_API_KEY)
                
        self.calculator = FinancialCalculator()
        self.model_name = settings.GLM_MODEL if settings.CHAT_PROVIDER == "zai" else settings.OPENAI_MODEL
        
        # If retriever is not provided, initialize standard stack
        if retriever:
            self.retriever = retriever
        else:
            embedder = Embedder()
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
            # GLM-5/Z.AI works similarly to OpenAI
            create_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.2,
            }
            
            # OpenAI supports forced JSON mode, check if we're using OpenAI
            if settings.CHAT_PROVIDER == "openai":
                create_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**create_params)
            
            raw_content = response.choices[0].message.content
            logger.info("Successfully received LLM analysis")
            
            return OutputParser.parse_analysis(raw_content, rag_context=rag_context)

        except Exception as e:
            logger.error(f"LLM request/analysis failed: {e}")
            return AnalysisResponse(
                answer=f"Analysis failed due to a system error: {str(e)}",
                key_metrics={},
                recommendations=[],
                risks=[],
                confidence_score=0.0,
                status="error"
            )
