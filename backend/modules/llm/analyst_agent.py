from datetime import datetime
import json
from typing import List, Dict, Any, Optional

import polars as pl
from openai import OpenAI
from zai import ZaiClient

from config import settings
from models.response_models import AnalysisResponse, TokenUsage
from modules.analytics.financial_calculator import FinancialCalculator
from modules.llm.code_interpreter import CodeInterpreter
from modules.llm.memory.database import ChatMemory
from modules.llm.output_parser import OutputParser
from modules.llm.prompts import ANALYST_SYSTEM_PROMPT, QUERY_PROMPT_TEMPLATE
from modules.rag.embedder import Embedder
from modules.rag.retriever import Retriever
from modules.rag.vector_store import VectorStore
from modules.storage.metadata_manager import MetadataManager
import structlog
from logging_config import Timer

logger = structlog.get_logger(__name__)


class AnalystAgent:
    """Main LLM orchestration for business data analysis with session memory."""

    # Intelligent column role detection patterns (Thai + English)
    COLUMN_ROLE_PATTERNS = {
        "revenue": ["revenue", "sales", "income", "turnover", "ยอดขาย"],
        "cost": ["cost", "cogs", "expense", "ต้นทุน"],
        "profit": ["profit", "margin", "กำไร", "net"],
        "quantity": ["qty", "quantity", "count", "units", "customers", "จำนวน"],
        "price": ["price", "unit_price", "rate", "ราคา"],
        "date": ["date", "month", "year", "period", "วันที่", "created", "timestamp"],
        "category": ["category", "type", "group", "class", "หมวดหมู่", "ประเภท"],
        "location": ["branch", "store", "region", "area", "city", "สาขา", "location"],
        "name": ["name", "item", "product", "sku", "ชื่อ", "รายการ", "สินค้า"],
        "rate": ["rate", "ratio", "percentage", "pct", "อัตรา", "waste_rate"],
        "id": ["id", "code", "no", "number", "รหัส"],
        "status": ["status", "state", "สถานะ"],
        "score": ["score", "rating", "rank", "คะแนน"],
    }

    def __init__(self, client=None, retriever: Retriever = None, model_name: str = None):
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
        default_model = settings.GLM_MODEL if settings.CHAT_PROVIDER == "zai" else settings.OPENAI_MODEL
        self.model_name = model_name if model_name else default_model
        self.metadata_manager = MetadataManager()
        self.interpreter = CodeInterpreter()

        if retriever:
            self.retriever = retriever
        else:
            embedder = Embedder()
            vector_store = VectorStore()
            self.retriever = Retriever(embedder=embedder, vector_store=vector_store)

    # ─────────────────────────────────────────────
    # DATA PROFILING
    # ─────────────────────────────────────────────

    def _auto_profile_column(self, col_name: str, dtype, df: pl.DataFrame) -> Dict[str, Any]:
        """Detect the business role of a column from name patterns and data."""
        col_lower = col_name.lower()
        detected_role = "unknown"
        for role, patterns in self.COLUMN_ROLE_PATTERNS.items():
            if any(p in col_lower for p in patterns):
                detected_role = role
                break

        profile = {"dtype": str(dtype), "role": detected_role}

        if dtype == pl.Utf8 or dtype == pl.Categorical:
            try:
                unique_vals = df[col_name].unique().to_list()
                if len(unique_vals) <= 15:
                    profile["unique_values"] = unique_vals
                else:
                    profile["unique_count"] = len(unique_vals)
                    profile["sample_values"] = unique_vals[:10]
            except Exception:
                pass

        return profile

    def _profile_dataframe(self, name: str, df: pl.DataFrame, include_samples: bool = True) -> Dict[str, Any]:
        """Build a complete profile for a single DataFrame."""
        numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
        dim_cols = [
            col for col, dtype in df.schema.items()
            if (dtype == pl.Utf8 or dtype == pl.Categorical) and 1 < df[col].n_unique() < 30
        ]
        metric_col = next((c for c in numeric_cols if "id" not in c.lower() and "index" not in c.lower()), None)

        # Column profiling
        column_profile = {
            col_name: self._auto_profile_column(col_name, dtype, df)
            for col_name, dtype in df.schema.items()
        }

        summary = {
            "records": len(df),
            "columns": df.columns,
            "column_profile": column_profile,
            "numeric_metrics": numeric_cols,
            "categorical_dimensions": dim_cols,
        }

        if include_samples:
            summary["sample_data"] = df.head(3).to_dicts()

        # Dimension values (exact labels)
        dimension_values = {}
        for dim in dim_cols:
            try:
                vals = df[dim].unique().sort().to_list()
                dimension_values[dim] = vals if len(vals) <= 60 else vals[:50] + [f"... and {len(vals) - 50} more"]
            except Exception:
                pass
        if dimension_values:
            summary["dimension_values"] = dimension_values

        # Top breakdown
        if metric_col and dim_cols:
            main_dim = dim_cols[0]
            summary[f"top_5_{main_dim}_by_{metric_col}"] = (
                df.group_by(main_dim)
                .agg(pl.col(metric_col).sum())
                .sort(metric_col, descending=True)
                .head(5)
                .to_dicts()
            )

        return summary

    def _prepare_metrics_context(
        self,
        data: Optional[List[Dict[str, Any]]] = None,
        filename: str = None,
        dfs: Optional[Dict[str, Any]] = None,
        include_samples: bool = True,
    ) -> str:
        """Build structured data context for the LLM."""
        metrics = {}

        # Data Dictionary (Schema Binding)
        if filename:
            filenames = [f.strip() for f in filename.split(",")]
            combined_dict = {}
            for fname in filenames:
                file_dict = self.metadata_manager.get_dictionary(fname)
                if file_dict:
                    combined_dict[fname] = file_dict
            metrics["data_dictionaries"] = combined_dict

        if dfs:
            multi_summaries = {
                name: self._profile_dataframe(name, df, include_samples)
                for name, df in dfs.items()
            }

            # Join Key Detection
            join_keys = {}
            df_names = list(dfs.keys())
            for i in range(len(df_names)):
                for j in range(i + 1, len(df_names)):
                    n1, n2 = df_names[i], df_names[j]
                    common = list(set(dfs[n1].columns) & set(dfs[n2].columns))
                    if common:
                        join_keys[f"{n1} <-> {n2}"] = common

            metrics["suggested_join_keys"] = join_keys
            metrics["active_dataframes"] = multi_summaries

        elif data:
            df = pl.DataFrame(data)
            numeric_cols = [col for col, dtype in df.schema.items() if dtype.is_numeric()]
            dim_cols = [
                col for col, dtype in df.schema.items()
                if (dtype == pl.Utf8 or dtype == pl.Categorical) and 1 < df[col].n_unique() < 30
            ]

            scope = {
                "total_records": len(df),
                "columns": df.columns,
                "numeric_metrics": numeric_cols,
                "categorical_dimensions": dim_cols,
            }
            if include_samples:
                scope["sample_data"] = df.head(3).to_dicts()

            # Date detection
            date_col = next(
                (col for col, dtype in df.schema.items()
                 if dtype.is_temporal() or "date" in col.lower() or "month" in col.lower()),
                None,
            )
            if date_col:
                try:
                    scope["date_range"] = {"start": str(df[date_col].min()), "end": str(df[date_col].max())}
                except Exception as e:
                    logger.warning(f"Failed to detect date range: {e}")

            # Metric breakdowns
            metric_col = next((c for c in numeric_cols if "id" not in c.lower()), None)
            if metric_col and dim_cols:
                breakdowns = {}
                for col in dim_cols[:3]:
                    breakdowns[f"totals_by_{col}"] = (
                        df.group_by(col).agg(pl.col(metric_col).sum())
                        .sort(metric_col, descending=True).head(40).to_dicts()
                    )
                scope["primary_metrics_breakdown"] = {"metric_used": metric_col, "breakdowns": breakdowns}

            # Stats
            for col in numeric_cols[:5]:
                scope[f"{col}_stats"] = self.calculator.summary_stats(df, col)

            metrics["dataset_scope"] = scope
        else:
            return "No data available."

        return json.dumps(metrics, indent=2)

    # ─────────────────────────────────────────────
    # PROMPT BUILDING
    # ─────────────────────────────────────────────

    def _build_history_text(self, session_id: str) -> str:
        """Build truncated conversation history."""
        history = self.memory.get_history(session_id, limit=6)
        parts = []
        for m in history:
            role = m["role"].capitalize()
            content = m["content"]
            if m["role"] in ("assistant", "ai") and m.get("data", {}).get("python_code"):
                snippet = m["data"]["python_code"][:150]
                if len(m["data"]["python_code"]) > 150:
                    snippet += " [TRUNCATED]"
                content = f"{content}\n[PREVIOUS_CODE]: {snippet}"
            if len(content) > 250:
                content = content[:250] + "... [TRUNCATED]"
            parts.append(f"{role}: {content}")
        return "\n".join(parts)

    def _build_var_info(self, dfs: Optional[Dict[str, Any]]) -> str:
        """List available DataFrame variable names AND their exact columns for the LLM."""
        if not dfs:
            return "No specific dataframes active."
        lines = ["AVAILABLE DATAFRAMES (USE THESE EXACT VARIABLE NAMES AND COLUMN NAMES IN YOUR CODE):"]
        for k, v in dfs.items():
            cols = v.columns if hasattr(v, 'columns') else []
            lines.append(f"- `{k}` → columns: {cols}")
        lines.append("\n⚠️ CRITICAL: Use ONLY the column names listed above. Do NOT guess or invent column names.")
        return "\n".join(lines)

    def _build_prompt(
        self, user_query: str, session_id: str, filename: str,
        metrics_context: str, rag_context: str, dfs: Optional[Dict[str, Any]],
    ) -> str:
        """Assemble the full user prompt for the LLM."""
        return QUERY_PROMPT_TEMPLATE.format(
            history=self._build_history_text(session_id),
            calculated_metrics=metrics_context,
            rag_context=rag_context,
            user_question=user_query,
            current_date=datetime.now().strftime("%Y-%m-%d"),
            filename=filename or "Unknown Dataset",
            available_files=self._build_var_info(dfs),
        )

    # ─────────────────────────────────────────────
    # LLM CALLS
    # ─────────────────────────────────────────────

    def _call_llm(self, create_params: Dict, total_usage: TokenUsage) -> str:
        """Call LLM and accumulate token usage. Returns raw content string."""
        response = self.client.chat.completions.create(**create_params)
        if hasattr(response, "usage") and response.usage:
            total_usage.prompt_tokens += response.usage.prompt_tokens
            total_usage.completion_tokens += response.usage.completion_tokens
            total_usage.total_tokens += response.usage.total_tokens
        return response.choices[0].message.content

    # ─────────────────────────────────────────────
    # CODE EXECUTION + AUTO-RETRY
    # ─────────────────────────────────────────────

    def _execute_with_retry(
        self, python_code: str, raw_content: str,
        create_params: Dict, total_usage: TokenUsage,
        dfs: Optional[Dict] = None, df: Optional[pl.DataFrame] = None,
    ) -> tuple:
        """Execute code. If it fails, ask LLM to fix and retry once. Returns (exec_result, final_code)."""
        exec_result = self.interpreter.execute(python_code, df=df, dfs=dfs)

        if exec_result["success"]:
            return exec_result, python_code

        # Auto-retry
        logger.warning("code_exec_failed", action="auto_retry", error=exec_result.get("error", "")[:300])
        retry_prompt = f"""Your code FAILED with this error:
```
{exec_result['error']}
```

Fix the code and try again. Common fixes:
- ColumnNotFoundError → Check exact column names and casing in the `columns` list.
- ComputeError → Check data types, cast with `.cast(pl.Float64)` if needed.
- SchemaError → Use `.alias()` to avoid name collisions.

Respond with ONLY the corrected JSON (with fixed `python_code`). Keep all other fields empty."""

        create_params["messages"].append({"role": "assistant", "content": raw_content})
        create_params["messages"].append({"role": "user", "content": retry_prompt})

        retry_content = self._call_llm(create_params, total_usage)
        try:
            retry_code = json.loads(retry_content).get("python_code")
            if retry_code:
                python_code = retry_code
                exec_result = self.interpreter.execute(retry_code, df=df, dfs=dfs)
                logger.info("auto_retry_result", success=exec_result['success'])
                create_params["messages"].append({"role": "assistant", "content": retry_content})
        except json.JSONDecodeError:
            logger.error("Auto-retry returned invalid JSON, skipping.")

        return exec_result, python_code

    # ─────────────────────────────────────────────
    # MAIN ORCHESTRATOR
    # ─────────────────────────────────────────────

    def analyze(
        self, user_query: str, data_context: List[Dict[str, Any]] = None,
        session_id: str = "default", filename: str = None, dfs: Dict[str, Any] = None,
        model_name: str = None,
    ) -> AnalysisResponse:
        """
        Orchestrate analysis: Context → LLM → Code Execution → Retry → Refine → Parse.
        """
        total_usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)
        effective_model = model_name or self.model_name

        # 1. Prepare context
        with Timer() as t_ctx:
            rag_context = self.retriever.get_context(user_query, top_k=5, filename=filename)
            metrics_context = self._prepare_metrics_context(data_context, filename=filename, dfs=dfs, include_samples=True)
        logger.info("context_prepared", duration_ms=t_ctx.duration_ms)

        # 2. Build prompt & call LLM (Turn 1: Strategy + Code Generation)
        prompt = self._build_prompt(user_query, session_id, filename, metrics_context, rag_context, dfs)
        create_params = {
            "model": effective_model,
            "messages": [
                {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        if settings.CHAT_PROVIDER == "openai":
            create_params["response_format"] = {"type": "json_object"}

        try:
            with Timer() as t_llm1:
                raw_content = self._call_llm(create_params, total_usage)
            logger.info("llm_turn_1", duration_ms=t_llm1.duration_ms, tokens=total_usage.total_tokens)
            initial_parsed = json.loads(raw_content)
            python_code = initial_parsed.get("python_code")

            # 3. Execute code if present
            if python_code and (data_context or dfs):
                df = pl.DataFrame(data_context) if data_context and not dfs else None
                exec_result, python_code = self._execute_with_retry(
                    python_code, raw_content, create_params, total_usage, dfs=dfs, df=df,
                )

                # 4. Final refinement (Turn 2: Summarize results)
                refinement_prompt = f"""EXECUTION RESULTS:
Code: {python_code}
Output: {exec_result['output']}
Error: {exec_result['error']}

ORIGINAL USER QUESTION: {user_query}

ACTION: Provide your FINAL JSON response based on the results above. ALL fields must be in valid JSON.

CRITICAL RULES:
1. LANGUAGE: Your `answer` MUST be written in the EXACT SAME language as the ORIGINAL USER QUESTION above.
   - If the user asked in Thai → answer in Thai. If in English → answer in English. NEVER mix languages.
2. NO_DATA_FOUND: If the Output contains "NO_DATA_FOUND" or shows 0 rows or empty results:
   - Your `answer` MUST clearly state that no data was found for the user's EXACT criteria.
   - Include the available date range if printed in the Output.
   - Set `charts` to [] (empty). Do NOT create charts with fabricated or substituted data.
   - Set `confidence_score` to 0.0.
   - NEVER silently substitute a different date, year, branch, or any filter value.
3. NUMBERS: Cite exact numbers from the Output. Do NOT round or paraphrase. If a value is not in the Output, do not mention it.
4. CHARTS: If the user asked for a chart/graph/กราฟ AND the Output contains data, populate `charts`:
   Format: [{{"type": "bar|line|area|pie|radar", "title": "...", "data": [{{"label": "...", "value": 123}}]}}]
   - Parse the Output carefully. Examples of how to map output to chart data:
     * If Output shows `branch: Thonglor, total: 50000` → {{"label": "Thonglor", "value": 50000}}
     * If Output shows a Polars table with columns → map the category column to "label" and numeric column to "value"
   - Each data item MUST have exactly "label" (string) and "value" (number) keys.
   - Choose the chart type based on the data: categories→bar, time→area, proportions→pie.
   - NEVER leave `charts` empty if the user asked for a visualization AND data exists.
5. ANOMALIES: If any value looks suspicious (negative where positive expected, extreme outliers), note it in `risks`.
6. The `answer` field MUST NOT be empty.
7. Set confidence_score: 0.95+ if all numbers from code, 0.7-0.9 if mixed, <0.7 if fallback, 0.0 if no data found."""

                create_params["messages"].append({"role": "user", "content": refinement_prompt})
                with Timer() as t_llm2:
                    raw_content = self._call_llm(create_params, total_usage)
                logger.info("llm_turn_2", duration_ms=t_llm2.duration_ms, tokens=total_usage.total_tokens)

            # 5. Parse & save
            parsed_response = OutputParser.parse_analysis(raw_content, rag_context=rag_context, token_usage=total_usage)
            if python_code:
                parsed_response.python_code = python_code
            if not parsed_response.answer or parsed_response.answer.strip() == "":
                parsed_response.answer = "Analysis complete. Please see detailed results below."

            self.memory.add_message(session_id, "user", user_query)
            self.memory.add_message(session_id, "ai", parsed_response.answer, data=parsed_response.model_dump())

            return parsed_response

        except Exception as e:
            logger.error("analysis_failed", error=str(e))
            return AnalysisResponse(
                answer=f"Analysis failed due to a system error: {str(e)}",
                key_metrics={},
                recommendations=[],
                risks=[],
                confidence_score=0.0,
                status="error",
            )

    def clear_history(self, session_id: str = "default"):
        """Clear the history for a given session."""
        self.memory.clear_history(session_id)
        logger.info("history_cleared", session_id=session_id)

    async def analyze_stream(
        self, user_query: str, data_context: List[Dict[str, Any]] = None,
        session_id: str = "default", filename: str = None, dfs: Dict[str, Any] = None,
    ):
        """
        Streaming version of analyze(). Yields SSE event strings.
        Turn 1 (code gen) is non-streamed. Turn 2 (final answer) is streamed.
        """
        from modules.llm.stream_handler import StreamHandler

        total_usage = TokenUsage(prompt_tokens=0, completion_tokens=0, total_tokens=0)

        # 1. Prepare context (same as analyze)
        rag_context = self.retriever.get_context(user_query, top_k=5, filename=filename)
        metrics_context = self._prepare_metrics_context(data_context, filename=filename, dfs=dfs, include_samples=True)

        # 2. Build prompt
        prompt = self._build_prompt(user_query, session_id, filename, metrics_context, rag_context, dfs)
        create_params = {
            "model": self.model_name,
            "messages": [
                {"role": "system", "content": ANALYST_SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            "temperature": 0.1,
        }
        if settings.CHAT_PROVIDER == "openai":
            create_params["response_format"] = {"type": "json_object"}

        try:
            # Turn 1: Non-streamed (code generation needs full JSON)
            yield StreamHandler._sse_event("status", "Generating analysis strategy...")
            raw_content = self._call_llm(create_params, total_usage)
            initial_parsed = json.loads(raw_content)
            python_code = initial_parsed.get("python_code")

            exec_result = None
            if python_code and (data_context or dfs):
                yield StreamHandler._sse_event("code", python_code)
                yield StreamHandler._sse_event("status", "Executing code...")

                df = pl.DataFrame(data_context) if data_context and not dfs else None
                exec_result, python_code = self._execute_with_retry(
                    python_code, raw_content, create_params, total_usage, dfs=dfs, df=df,
                )

                # Build refinement prompt for Turn 2
                refinement_prompt = f"""EXECUTION RESULTS:
Code: {python_code}
Output: {exec_result['output']}
Error: {exec_result['error']}

ORIGINAL USER QUESTION: {user_query}

ACTION: Provide your FINAL JSON response based on the results above.

CRITICAL RULES:
1. LANGUAGE: Your `answer` MUST be written in the EXACT SAME language as the ORIGINAL USER QUESTION above.
   - If the user asked in Thai → answer in Thai. If in English → answer in English. NEVER mix languages.
2. NUMBERS: Cite exact numbers from the Output. Do NOT round or paraphrase.
3. CHARTS: If the user asked for a chart/graph/กราฟ, you MUST populate the `charts` field with the computed data from the Output above.
   Format: [{{"type": "bar|line|area|pie", "title": "...", "data": [{{"label": "...", "value": 123}}]}}]
   - Extract the actual label/value pairs from the printed Output above.
   - If the Output has lines like "Branch A: 12345", map them as {{"label": "Branch A", "value": 12345}}.
   - NEVER leave `charts` empty if the user asked for a visualization.
4. The `answer` field MUST NOT be empty.
5. Set confidence_score: 0.95+ if all numbers from code, 0.7-0.9 if mixed, <0.7 if fallback."""

                create_params["messages"].append({"role": "user", "content": refinement_prompt})

            # Turn 2 (or only turn): Stream the response
            async for event in StreamHandler.stream_analysis(
                self.client, self.model_name, create_params, total_usage,
                python_code=python_code, exec_result=exec_result, rag_context=rag_context,
            ):
                yield event

            # Save to memory
            self.memory.add_message(session_id, "user", user_query)
            self.memory.add_message(session_id, "ai", initial_parsed.get("answer", "Analysis complete."))

        except Exception as e:
            logger.error("stream_analysis_failed", error=str(e))
            yield StreamHandler._sse_event("error", str(e))
