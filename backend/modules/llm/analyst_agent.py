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
        
        from modules.storage.metadata_manager import MetadataManager
        self.metadata_manager = MetadataManager()
        
        # If retriever is not provided, initialize standard stack
        if retriever:
            self.retriever = retriever
        else:
            embedder = Embedder()
            vector_store = VectorStore()
            self.retriever = Retriever(embedder=embedder, vector_store=vector_store)

    def _prepare_metrics_context(self, data: List[Dict[str, Any]], filename: str = None) -> str:
        """Calculate summary metrics for the LLM context using Polars to prevent LLM math."""
        if not data:
            return "No numerical data available for metrics."
        
        import polars as pl
        df = pl.DataFrame(data)
        metrics = {}
        
        # 0. Data Dictionary (Schema Binding)
        if filename:
            metrics["data_dictionary"] = self.metadata_manager.get_dictionary(filename)
        numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
        dimension_cols = [col for col in df.columns if col in ["category", "dept", "department", "region", "status", "subcategory", "priority"]]
        
        metrics["dataset_scope"] = {
            "total_records": len(df),
            "columns": df.columns,
            "numeric_columns": numeric_cols,
            "available_dimensions": dimension_cols
        }
        
        if month_col := next((c for c in ["month", "date"] if c in df.columns), None):
            metrics["dataset_scope"]["date_range"] = {
                "start": str(df[month_col].min()),
                "end": str(df[month_col].max())
            }
        
        # 1. Individual Dimension Summaries (Multi-Column Protection)
        revenue_col = next((c for c in ["revenue", "totalamount", "total_amount", "amount"] if c in df.columns), None)
        
        if revenue_col:
            dim_summaries = {}
            for col in dimension_cols:
                # Group by each dimension to ensure AI sees specific column totals
                summary = df.group_by(col).agg(pl.col(revenue_col).sum()).sort(revenue_col, descending=True)
                dim_summaries[f"totals_by_{col}"] = summary.to_dicts()
            
            metrics["dimension_performance_matrix"] = dim_summaries

            # 2. Cross-Dimensional Matrix (e.g., Dept + Status)
            # Find status and a primary dimension (dept/category)
            status_col = next((c for c in ["status", "priority"] if c in df.columns), None)
            main_dim = next((c for c in ["department", "dept", "category"] if c in df.columns and c != status_col), None)
            
            if status_col and main_dim:
                cross_tab = df.group_by([main_dim, status_col]).agg(pl.col(revenue_col).sum()).sort([main_dim, status_col])
                metrics["cross_dimensional_performance"] = {
                    "description": f"Revenue breakdown by {main_dim} and {status_col}",
                    "data": cross_tab.to_dicts()
                }

            # 3. Trending Analysis
            month_col = next((c for c in ["month", "date", "timestamp"] if c in df.columns), None)
            if month_col:
                trend = df.group_by(month_col).agg(pl.col(revenue_col).sum()).sort(month_col)
                trend_list = trend.to_dicts()
                enhanced_trend = []
                for j in range(len(trend_list)):
                    current_rev = float(trend_list[j][revenue_col])
                    row = {"label": str(trend_list[j][month_col]), "value": round(current_rev, 2)}
                    enhanced_trend.append(row)
                metrics["revenue_trend_analysis"] = enhanced_trend

            # 4. Outlier detection
            top_5 = df.sort(revenue_col, descending=True).head(5)
            metrics["top_performing_transactions"] = top_5.to_dicts()
        
        # 5. General summary stats for all numeric cols
        for col in numeric_cols:
            if col != revenue_col: # Skip redundant stats for main revenue if already trended
                metrics[f"{col}_stats"] = self.calculator.summary_stats(df, col)
        
        return json.dumps(metrics, indent=2)

    def analyze(self, user_query: str, data_context: List[Dict[str, Any]] = None, session_id: str = "default", filename: str = None) -> AnalysisResponse:
        """
        Orchestrate the analysis by combining RAG, python math, and session history.
        Supports 2-step reasoning via Code Interpreter.
        """
        from modules.llm.code_interpreter import CodeInterpreter
        interpreter = CodeInterpreter()
        
        # 1. Get Conversation History (Smarter Truncation)
        history = self.memory.get_history(session_id, limit=6)
        history_parts = []
        for m in history:
            role = m['role'].capitalize()
            content = m['content']
            
            # If assistant message has code, include a snippet of the code too
            if m['role'] == 'assistant' and m.get('data') and m['data'].get('python_code'):
                code_snippet = m['data']['python_code']
                if len(code_snippet) > 150:
                    code_snippet = code_snippet[:150] + " [TRUNCATED_CODE]"
                content = f"{content}\n[PREVIOUS_CODE]: {code_snippet}"
            
            if len(content) > 250:
                content = content[:250] + "... [TRUNCATED]"
            
            history_parts.append(f"{role}: {content}")
        history_text = "\n".join(history_parts)
        
        # 2. Get RAG context (filtered by filename if provided)
        rag_context = self.retriever.get_context(user_query, top_k=5, filename=filename)

        # 3. Get calculated metrics
        metrics_context = self._prepare_metrics_context(data_context, filename=filename) if data_context else "No table data provided."
        
        # 4. First Pass: Strategic Strategy & Code Generation
        from datetime import datetime
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        
        from modules.llm.prompts import QUERY_PROMPT_TEMPLATE
        prompt = QUERY_PROMPT_TEMPLATE.format(
            history=history_text,
            calculated_metrics=metrics_context,
            rag_context=rag_context,
            user_question=user_query,
            current_date=current_date_str
        )
        
        try:
            create_params = {
                "model": self.model_name,
                "messages": [
                    {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                    {"role": "user", "content": prompt}
                ],
                "temperature": 0.1,
            }
            
            if settings.CHAT_PROVIDER == "openai":
                create_params["response_format"] = {"type": "json_object"}
            
            response = self.client.chat.completions.create(**create_params)
            raw_content = response.choices[0].message.content
            
            # Use OutputParser for flexibility, but handle the 2-step case
            initial_parsed = json.loads(raw_content)
            python_code = initial_parsed.get("python_code")
            
            # Step 2: Execution if needed
            if python_code and data_context:
                import polars as pl
                df = pl.DataFrame(data_context)
                exec_result = interpreter.execute(python_code, df)
                
                # Step 3: Refinement with results
                refinement_prompt = f"""
                EXECUTION RESULTS:
                Code: {python_code}
                Output: {exec_result['output']}
                Error: {exec_result['error']}
                
                ACTION: Provide your FINAL Strategic Intelligence answer based on the results above.
                - Your response MUST be valid JSON.
                - The 'answer' field MUST NOT be empty. Synthesize the results into professional Thai insights.
                - If the results provide enough data for a table, include it in 'table_data'.
                """
                
                create_params["messages"].append({"role": "assistant", "content": raw_content})
                create_params["messages"].append({"role": "user", "content": refinement_prompt})
                
                final_response = self.client.chat.completions.create(**create_params)
                raw_content = final_response.choices[0].message.content
                logger.info("Successfully received LLM analysis after code execution")

            from modules.llm.output_parser import OutputParser
            parsed_response = OutputParser.parse_analysis(raw_content, rag_context=rag_context)
            if python_code:
                parsed_response.python_code = python_code

            if not parsed_response.answer or parsed_response.answer.strip() == "":
                parsed_response.answer = "การวิเคราะห์เสร็จสมบูรณ์แล้วครับ (โปรดดูรายละเอียดในส่วนข้อมูลเพิ่มเติมด้านล่าง)"

            # 5. Save to Memory
            self.memory.add_message(session_id, "user", user_query)
            self.memory.add_message(session_id, "assistant", parsed_response.answer, data=parsed_response.model_dump())
            
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
