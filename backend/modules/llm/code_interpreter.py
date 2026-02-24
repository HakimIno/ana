import io
import sys
import logging
import traceback
import polars as pl
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class CodeInterpreter:
    """Executes Python/Polars code in a controlled environment."""

    def execute(self, code: str, df: pl.DataFrame) -> Dict[str, Any]:
        """
        Executes the provided code with the dataframe 'df' available in scope.
        Returns a dictionary containing the output or error.
        """
        # Create a captured stdout
        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer

        locals_dict = {"df": df, "pl": pl}
        
        try:
            # Execute the code
            # Note: In a production environment, use a more restricted sandbox if possible.
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
