import io
import sys
import logging
import traceback
import polars as pl
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CodeInterpreter:
    """Executes Python/Polars code in a controlled environment."""

    def execute(self, code: str, df: Optional[pl.DataFrame] = None, dfs: Optional[Dict[str, pl.DataFrame]] = None) -> Dict[str, Any]:
        """
        Executes the provided code. 
        Supports a single 'df' or a dictionary of 'dfs' (e.g. {'sales': df1, 'inventory': df2}).
        """
        # Create a captured stdout
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer

        locals_dict = {"pl": pl}
        if df is not None:
            locals_dict["df"] = df
        if dfs:
            locals_dict.update(dfs)
            locals_dict["dfs"] = dfs # Also provide the dict itself
        
        try:
            # Execute the code
            exec(code, {"pl": pl}, locals_dict)
            
            output = output_buffer.getvalue()
            return {
                "success": True,
                "output": output,
                "error": None
            }
        except Exception:
            error_msg = traceback.format_exc()
            logger.error(f"Execution error:\n{error_msg}")
            return {
                "success": False,
                "output": output_buffer.getvalue(),
                "error": error_msg
            }
        finally:
            sys.stdout = old_stdout
            output_buffer.close()
