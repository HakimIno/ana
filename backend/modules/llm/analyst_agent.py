from datetime import datetime
import json
import logging
from typing import List, Dict, Any, Optional

import polars as pl
from openai import OpenAI
from zai import ZaiClient

from config import settings
from models.response_models import AnalysisResponse
from modules.analytics.financial_calculator import FinancialCalculator
from modules.llm.code_interpreter import CodeInterpreter
from modules.llm.memory.database import ChatMemory
from modules.llm.output_parser import OutputParser
from modules.llm.prompts import ANALYST_SYSTEM_PROMPT, QUERY_PROMPT_TEMPLATE
from modules.rag.embedder import Embedder
from modules.rag.retriever import Retriever
from modules.rag.vector_store import VectorStore
from modules.storage.metadata_manager import MetadataManager

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
        
        self.metadata_manager = MetadataManager()
        
        # If retriever is not provided, initialize standard stack
        if retriever:
            self.retriever = retriever
        else:
            embedder = Embedder()
            vector_store = VectorStore()
            self.retriever = Retriever(embedder=embedder, vector_store=vector_store)

    def _prepare_metrics_context(self, data: Optional[List[Dict[str, Any]]] = None, filename: str = None, dfs: Optional[Dict[str, Any]] = None) -> str:
        """
        Creates a structured summary of the data for the AI's first turn.
        Supports single list 'data' or dictionary of 'dfs'.
        """
        metrics = {}

        # 0. Data Dictionary (Schema Binding)
        if filename:
            filenames = [f.strip() for f in filename.split(",")]
            combined_dict = {}
            for fname in filenames:
                file_dict = self.metadata_manager.get_dictionary(fname)
                if file_dict:
                    combined_dict[fname] = file_dict
            metrics["data_dictionaries"] = combined_dict

        # Process data
        if dfs:
            # Multi-file summary
            multi_summaries = {}
            for name, df in dfs.items():
                numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
                # Dynamic Dimension Detection: String/Categorical with reasonable cardinality
                dim_cols = [
                    col for col, dtype in df.schema.items() 
                    if (dtype == pl.Utf8 or dtype == pl.Categorical) and 1 < df[col].n_unique() < 30
                ]
                
                # Top metric detection (avoiding IDs)
                metric_col = next((c for c in numeric_cols if "id" not in c.lower() and "index" not in c.lower()), None)
                
                df_summary = {
                    "records": len(df),
                    "columns": df.columns,
                    "numeric_metrics": numeric_cols,
                    "categorical_dimensions": dim_cols
                }
                
                if metric_col and dim_cols:
                    main_dim = dim_cols[0]
                    df_summary[f"top_5_{main_dim}_by_{metric_col}"] = (
                        df.group_by(main_dim)
                        .agg(pl.col(metric_col).sum())
                        .sort(metric_col, descending=True)
                        .head(5)
                        .to_dicts()
                    )
                
                multi_summaries[name] = df_summary
            
            metrics["active_dataframes"] = multi_summaries
        elif data:
            df = pl.DataFrame(data)
            numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
            dim_cols = [
                col for col, dtype in df.schema.items() 
                if (dtype == pl.Utf8 or dtype == pl.Categorical) and 1 < df[col].n_unique() < 30
            ]
            
            metrics["dataset_scope"] = {
                "total_records": len(df),
                "columns": df.columns,
                "numeric_metrics": numeric_cols,
                "categorical_dimensions": dim_cols
            }
            
            # Dynamic date detection
            date_col = next((col for col, dtype in df.schema.items() if dtype.is_temporal() or "date" in col.lower() or "month" in col.lower()), None)
            if date_col:
                try:
                    metrics["dataset_scope"]["date_range"] = {
                        "start": str(df[date_col].min()),
                        "end": str(df[date_col].max())
                    }
                except Exception as e:
                    logger.warning(f"Failed to detect date range: {e}")
                    pass
            
            # Top metric summaries
            metric_col = next((c for c in numeric_cols if "id" not in c.lower()), None)
            if metric_col and dim_cols:
                summaries = {}
                for col in dim_cols[:3]: # limit to top 3 dimensions
                    summaries[f"totals_by_{col}"] = (
                        df.group_by(col)
                        .agg(pl.col(metric_col).sum())
                        .sort(metric_col, descending=True)
                        .head(10)
                        .to_dicts()
                    )
                metrics["primary_metrics_breakdown"] = {
                    "metric_used": metric_col,
                    "breakdowns": summaries
                }
            
            # Sample stats for numeric
            for col in numeric_cols[:5]: # limit to top 5
                metrics[f"{col}_stats"] = self.calculator.summary_stats(df, col)

        else:
            return "No data available."
        
        return json.dumps(metrics, indent=2)

    def analyze(self, user_query: str, data_context: List[Dict[str, Any]] = None, session_id: str = "default", filename: str = None, dfs: Dict[str, Any] = None) -> AnalysisResponse:
        """
        Orchestrate the analysis by combining RAG, python math, and session history.
        Supports 2-step reasoning via Code Interpreter.
        """
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
            
            history_parts.append(f"{role.capitalize()}: {content}")
        history_text = "\n".join(history_parts)
        
        # 2. Get RAG context (filtered by filename if provided)
        rag_context = self.retriever.get_context(user_query, top_k=5, filename=filename)

        # 3. Get calculated metrics
        metrics_context = self._prepare_metrics_context(data_context, filename=filename, dfs=dfs)
        
        # 4. First Pass: Strategic Strategy & Code Generation
        current_date_str = datetime.now().strftime("%Y-%m-%d")
        
        # 4. Get Available Files (Detailed Var info)
        var_info = ""
        if dfs:
            var_info = "AVAILABLE DATAFRAMES (USE THESE VARIABLES IN YOUR CODE):\n"
            for k in dfs.keys():
                var_info += f"- `{k}`\n"
        
        prompt = QUERY_PROMPT_TEMPLATE.format(
            history=history_text,
            calculated_metrics=metrics_context,
            rag_context=rag_context,
            user_question=user_query,
            current_date=current_date_str,
            filename=filename or "Unknown Dataset",
            available_files=var_info or "No specific dataframes active."
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
            if python_code and (data_context or dfs):
                if dfs:
                    exec_result = interpreter.execute(python_code, dfs=dfs)
                else:
                    df = pl.DataFrame(data_context)
                    exec_result = interpreter.execute(python_code, df=df)
                
                # Step 3: Refinement with results
                refinement_prompt = f"""
                EXECUTION RESULTS:
                Code: {python_code}
                Output: {exec_result['output']}
                Error: {exec_result['error']}
                
                ACTION: Provide your FINAL Strategic Intelligence answer based on the results above.
                - Your response MUST be valid JSON.
                - **RESILIENT ADVISOR**: If there was an ERROR in the code, do NOT just say "I cannot display data". Instead, use your existing knowledge of the dataset (from the first turn) to provide the best possible strategic advice while clearly acknowledging you couldn't calculate the latest figures.
                - **STRICT VERACITY**: If a value could not be calculated due to an error, DO NOT use descriptive text placeholders in `table_data` or `charts`. Use "Error" or null.
                - The 'answer' field MUST NOT be empty. Synthesize the results into professional Thai insights.
                - If the results provide enough data for a table, include it in 'table_data'.
                """
                
                create_params["messages"].append({"role": "assistant", "content": raw_content})
                create_params["messages"].append({"role": "user", "content": refinement_prompt})
                
                final_response = self.client.chat.completions.create(**create_params)
                raw_content = final_response.choices[0].message.content
                logger.info("Successfully received LLM analysis after code execution")

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
