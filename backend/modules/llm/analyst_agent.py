from typing import List, Dict, Any
from openai import OpenAI
from zai import ZaiClient
from modules.llm.prompts import ANALYST_SYSTEM_PROMPT
from modules.analytics.financial_calculator import FinancialCalculator
from modules.rag.vector_store import VectorStore
from modules.rag.embedder import Embedder
from modules.rag.retriever import Retriever
from config import settings
import logging
import json
from modules.llm.memory.database import ChatMemory
from models.response_models import AnalysisResponse
from modules.llm.output_parser import OutputParser

logger = logging.getLogger(__name__)

class AnalystAgent:
    """Main LLM orchestration for financial analysis with session memory."""

    def __init__(self, client=None, retriever: Retriever = None):
        """Initialize the AnalystAgent with a client, retriever and memory."""
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
        self.memory = ChatMemory()
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
        
        # 0. Dataset Scope (for Intent Recognition)
        metrics["dataset_scope"] = {
            "total_records": len(df),
            "columns": df.columns,
            "numeric_columns": [col for col, dtype in df.schema.items() if dtype.is_numeric()],
            "category_columns": [col for col in ["category", "dept", "department", "region"] if col in df.columns]
        }
        
        if month_col := next((c for c in ["month", "date"] if c in df.columns), None):
            metrics["dataset_scope"]["date_range"] = {
                "start": str(df[month_col].min()),
                "end": str(df[month_col].max())
            }
        
        # Identify key dimensions for the AI
        metrics["dataset_scope"]["available_dimensions"] = {
            "geographic": [c for c in ["region", "area", "state"] if c in df.columns],
            "product_hierarchy": [c for c in ["category", "subcategory", "item"] if c in df.columns],
            "temporal": [c for c in ["month", "date", "year"] if c in df.columns]
        }

        # Detect numeric columns and generate summary stats
        numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
        for col in numeric_cols:
            metrics[col] = self.calculator.summary_stats(df, col)
        
        # Check for Revenue/TotalAmount and Month/Date for trending
        revenue_col = next((c for c in ["revenue", "totalamount", "total_amount", "amount"] if c in df.columns), None)
        month_col = next((c for c in ["month", "date", "timestamp"] if c in df.columns), None)

        if revenue_col:
            # 1. Trending & Growth Analysis
            if month_col:
                # Group by month and sum revenue
                trend = df.group_by(month_col).agg(pl.col(revenue_col).sum()).sort(month_col)
                trend_list = trend.to_dicts()
                
                # Calculate MoM Growth
                enhanced_trend = []
                for j in range(len(trend_list)):
                    current_rev = float(trend_list[j][revenue_col])
                    row = {"label": str(trend_list[j][month_col]), "value": round(current_rev, 2)}
                    if j > 0:
                        prev_rev = float(trend_list[j-1][revenue_col])
                        if prev_rev > 0:
                            growth = ((current_rev - prev_rev) / prev_rev) * 100
                            row["mom_growth_pct"] = round(growth, 2)
                    enhanced_trend.append(row)
                
                metrics["revenue_trend_analysis"] = enhanced_trend
            
            # 2. Regional Breakdown (10/10 Intel)
            region_col = next((c for c in ["region", "area", "state", "city"] if c in df.columns), None)
            if region_col:
                reg_data = df.group_by(region_col).agg(pl.col(revenue_col).sum()).sort(revenue_col, descending=True)
                metrics["regional_revenue_performance"] = reg_data.to_dicts()

            # 3. Category & Product Depth (10/10 Intel)
            cat_col = next((c for c in ["category", "dept", "department"] if c in df.columns), None)
            sub_col = next((c for c in ["subcategory", "sub_category", "product", "item"] if c in df.columns), None)
            
            if cat_col:
                total_rev = df[revenue_col].sum()
                cat_data = df.group_by(cat_col).agg(pl.col(revenue_col).sum()).sort(revenue_col, descending=True)
                cat_summary = []
                for row in cat_data.to_dicts():
                    share = (float(row[revenue_col]) / total_rev) * 100
                    cat_item = {
                        "category": row[cat_col],
                        "revenue": round(float(row[revenue_col]), 2),
                        "market_share_pct": round(share, 2)
                    }
                    # Add depth if sub-category exists
                    if sub_col:
                        top_subs = df.filter(pl.col(cat_col) == row[cat_col]).group_by(sub_col).agg(pl.col(revenue_col).sum()).sort(revenue_col, descending=True).head(3)
                        cat_item["top_products"] = top_subs.to_dicts()
                    
                    cat_summary.append(cat_item)
                metrics["category_drilldown_analysis"] = cat_summary

            # 4. Outlier/High Value detection
            top_5 = df.sort(revenue_col, descending=True).head(5)
            metrics["top_performing_transactions"] = top_5.to_dicts()
            
        return json.dumps(metrics, indent=2)

    def analyze(self, user_query: str, data_context: List[Dict[str, Any]] = None, session_id: str = "default", filename: str = None) -> AnalysisResponse:
        """
        Orchestrate the analysis by combining RAG, python math, and session history.
        """
        # 1. Get Conversation History
        history = self.memory.get_history(session_id, limit=6)
        history_text = "\n".join([f"{m['role'].capitalize()}: {m['content'][:200]}..." for m in history])
        
        # 2. Get RAG context (filtered by filename if provided)
        rag_context = self.retriever.get_context(user_query, top_k=5, filename=filename)

        # 3. Get calculated metrics
        metrics_context = self._prepare_metrics_context(data_context) if data_context else "No table data provided."
        logger.debug(f"Metrics Context: {metrics_context}")

        # 4. Assemble prompt
        from modules.llm.prompts import QUERY_PROMPT_TEMPLATE
        prompt = QUERY_PROMPT_TEMPLATE.format(
            history=history_text,
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
            
            parsed_response = OutputParser.parse_analysis(raw_content, rag_context=rag_context)
            
            # 5. Save to Memory
            self.memory.add_message(session_id, "user", user_query)
            
            # Save assistant message with full metadata for charts/metrics in history
            response_data = parsed_response.model_dump()
            # We already save 'answer' as content, but it's safe to keep in data too for simplicity
            self.memory.add_message(session_id, "assistant", parsed_response.answer, data=response_data)
            
            return parsed_response

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
    def clear_history(self, session_id: str = "default"):
        """Clear the history for a given session."""
        self.memory.clear_history(session_id)
        logger.info(f"Cleared history for session: {session_id}")
