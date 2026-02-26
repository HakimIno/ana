"""
Hardened Python/Polars code execution sandbox.

Security layers:
1. Static Analysis — AST-level validation before execution
2. Module Blocklist — blocks dangerous imports at string AND AST level
3. Builtin Restriction — only safe builtins exposed
4. Subprocess Isolation — runs code in a separate process with resource limits
5. Timeout — hard 10-second limit via signal + process kill
6. Output Cap — max 50KB stdout to prevent memory bomb
"""
import ast
import collections
import datetime
import io
import json
import math
import multiprocessing
import sys
import signal
import structlog
import traceback
import re
import resource
import polars as pl
from typing import Dict, Any, Optional

logger = structlog.get_logger(__name__)

# ─────────────────────────────────────────────────
# SECURITY CONFIGURATION
# ─────────────────────────────────────────────────

# Modules that are NEVER allowed (checked at string + AST level)
BLOCKED_MODULES = frozenset({
    "os", "sys", "subprocess", "shutil", "pathlib",
    "socket", "http", "requests", "urllib", "urllib3",
    "ctypes", "importlib", "pickle", "shelve",
    "tempfile", "glob", "signal", "threading", "multiprocessing",
    "webbrowser", "ftplib", "smtplib", "telnetlib",
    "xml", "html", "json",  # json blocked in exec (we handle it outside)
    "sqlite3", "dbm", "zipfile", "tarfile", "gzip", "bz2", "lzma",
    "code", "codeop", "compile", "compileall",
    "inspect", "dis", "gc", "atexit",
})

# Builtin functions/names that are NEVER allowed
BLOCKED_BUILTINS = frozenset({
    "exec", "eval", "compile", "__import__",
    "open", "input", "breakpoint",
    "globals", "locals", "vars", "dir",
    "getattr", "setattr", "delattr", "hasattr",
    "memoryview", "bytearray", "bytes",
})

# Only these builtins are exposed to executed code
SAFE_BUILTINS = {
    "print": print, "len": len, "range": range, "str": str,
    "int": int, "float": float, "list": list, "dict": dict,
    "tuple": tuple, "set": set, "frozenset": frozenset,
    "sorted": sorted, "reversed": reversed,
    "enumerate": enumerate, "zip": zip, "map": map, "filter": filter,
    "sum": sum, "min": min, "max": max, "abs": abs, "round": round,
    "isinstance": isinstance, "issubclass": issubclass, "type": type,
    "bool": bool, "any": any, "all": all,
    "True": True, "False": False, "None": None,
    "ValueError": ValueError, "TypeError": TypeError,
    "KeyError": KeyError, "IndexError": IndexError,
    "Exception": Exception,
}

POLARS_CORRECTIONS = [
    # Pandas → Polars method renames
    (".groupby(", ".group_by("),
    (".first()", ".head(1)"),
    (".isnull()", ".is_null()"),
    (".notnull()", ".is_not_null()"),
    (".fillna(", ".fill_null("),
    (".dropna(", ".drop_nulls("),
    (".isna()", ".is_null()"),
    (".notna()", ".is_not_null()"),
    (".astype(", ".cast("),
    (".sort_values(", ".sort("),
    (".iterrows()", ".to_dicts()"),
    (".apply(", ".map_elements("),
    (".reset_index()", ""),          # no-op in polars
    (".reset_index(drop=True)", ""), # no-op in polars
    (".nunique()", ".n_unique()"),
    (".to_numpy()", ".to_list()"),
    ("import pandas as pd", "# pandas not available, use polars"),
    ("pd.DataFrame", "pl.DataFrame"),
    ("pd.read_csv", "# pl.read_csv not allowed, use pre-loaded data"),
    # Polars LazyFrame vs eager DataFrame corrections
    (".lazy().collect()", ""),  # df.lazy().collect() → df (already eager)
    (".collect()", ""),         # stray .collect() on DataFrames → no-op
    (".lazy()", ""),            # df.lazy() → df (keep eager)
]

# Import lines that should be silently stripped because the modules
# are already pre-injected into the sandbox globals.
STRIPPED_IMPORT_PATTERNS = [
    r"^\s*import polars as pl\s*$",
    r"^\s*import polars\s*$",
    r"^\s*from polars import .*$",
    r"^\s*import datetime.*$",
    r"^\s*from datetime import .*$",
    r"^\s*import math\s*$",
    r"^\s*from math import .*$",
    r"^\s*import re\s*$",
    r"^\s*from collections import .*$",
]

EXEC_TIMEOUT_SECONDS = 10
MAX_OUTPUT_BYTES = 50 * 1024  # 50KB stdout cap
MAX_MEMORY_MB = 256


# ─────────────────────────────────────────────────
# AST VALIDATOR
# ─────────────────────────────────────────────────

class _ASTValidator(ast.NodeVisitor):
    """Walks the AST to detect dangerous constructs BEFORE execution."""

    def __init__(self):
        self.violations: list[str] = []

    def visit_Import(self, node: ast.Import):
        for alias in node.names:
            module_root = alias.name.split(".")[0]
            if module_root in BLOCKED_MODULES:
                self.violations.append(f"Blocked import: {alias.name}")
        self.generic_visit(node)

    def visit_ImportFrom(self, node: ast.ImportFrom):
        if node.module:
            module_root = node.module.split(".")[0]
            if module_root in BLOCKED_MODULES:
                self.violations.append(f"Blocked import from: {node.module}")
        self.generic_visit(node)

    def visit_Call(self, node: ast.Call):
        # Block dangerous builtin calls
        if isinstance(node.func, ast.Name):
            if node.func.id in BLOCKED_BUILTINS:
                self.violations.append(f"Blocked builtin call: {node.func.id}()")
        # Block __dunder__ attribute access on calls
        if isinstance(node.func, ast.Attribute):
            if node.func.attr.startswith("__") and node.func.attr.endswith("__"):
                self.violations.append(f"Blocked dunder access: .{node.func.attr}")
        self.generic_visit(node)

    def visit_Attribute(self, node: ast.Attribute):
        # Block __dunder__ attribute access (e.g. obj.__class__.__subclasses__)
        if node.attr.startswith("__") and node.attr.endswith("__"):
            self.violations.append(f"Blocked dunder attribute: .{node.attr}")
        self.generic_visit(node)


def _validate_ast(code: str) -> Optional[str]:
    """Parse and validate code AST. Returns error string or None."""
    try:
        tree = ast.parse(code)
    except SyntaxError as e:
        return f"SyntaxError: {e}"

    validator = _ASTValidator()
    validator.visit(tree)

    if validator.violations:
        return "SECURITY VIOLATION:\n" + "\n".join(f"  - {v}" for v in validator.violations)
    return None


# ─────────────────────────────────────────────────
# SUBPROCESS WORKER
# ─────────────────────────────────────────────────

def _worker(code: str, data_json: str, result_queue: multiprocessing.Queue):
    """
    Runs in a separate process with resource limits.
    Communicates results back via multiprocessing.Queue.
    """
    try:
        # Set resource limits (memory + CPU)
        soft, hard = resource.getrlimit(resource.RLIMIT_AS)
        resource.setrlimit(resource.RLIMIT_AS, (MAX_MEMORY_MB * 1024 * 1024, hard))
    except (ValueError, resource.error):
        pass  # Some systems don't support RLIMIT_AS

    output_buffer = io.StringIO()
    old_stdout = sys.stdout
    sys.stdout = output_buffer

    try:
        # Deserialize data
        env_data = json.loads(data_json)
        locals_dict = {}

        if "df" in env_data:
            locals_dict["df"] = pl.DataFrame(env_data["df"])
        if "dfs" in env_data:
            dfs = {k: pl.DataFrame(v) for k, v in env_data["dfs"].items()}
            locals_dict.update(dfs)
            locals_dict["dfs"] = dfs

        safe_globals = {
            "pl": pl,
            "datetime": datetime,
            "math": math,
            "re": re,
            "collections": collections,
            "__builtins__": SAFE_BUILTINS,
        }
        exec(code, safe_globals, locals_dict)

        output = output_buffer.getvalue()
        if len(output) > MAX_OUTPUT_BYTES:
            output = output[:MAX_OUTPUT_BYTES] + f"\n... [OUTPUT TRUNCATED at {MAX_OUTPUT_BYTES} bytes]"

        result_queue.put({"success": True, "output": output, "error": None})
    except Exception:
        result_queue.put({"success": False, "output": output_buffer.getvalue(), "error": traceback.format_exc()})
    finally:
        sys.stdout = old_stdout
        output_buffer.close()


def _timeout_handler(signum, frame):
    raise TimeoutError(f"Code execution exceeded {EXEC_TIMEOUT_SECONDS}s limit")


# ─────────────────────────────────────────────────
# MAIN INTERPRETER
# ─────────────────────────────────────────────────

class CodeInterpreter:
    """Hardened Python/Polars code executor with multi-layer security."""

    def _preprocess_code(self, code: str) -> str:
        """Auto-correct common Pandas-style syntax and strip pre-injected imports."""
        for old, new in POLARS_CORRECTIONS:
            code = code.replace(old, new)
        code = re.sub(
            r'\.rename\(columns\s*=\s*(\{[^}]+\})\)',
            r'.rename(\1)',
            code,
        )
        # Strip imports that are already pre-injected in the sandbox
        lines = code.split('\n')
        cleaned = []
        for line in lines:
            stripped = False
            for pattern in STRIPPED_IMPORT_PATTERNS:
                if re.match(pattern, line):
                    stripped = True
                    break
            if not stripped:
                cleaned.append(line)
        code = '\n'.join(cleaned)
        return code

    def _check_security(self, code: str) -> Optional[str]:
        """Multi-layer security check: string scan + AST validation."""
        # Layer 1: Quick string scan
        for module in BLOCKED_MODULES:
            if f"import {module}" in code or f"from {module}" in code:
                return f"SECURITY: import of '{module}' is blocked."

        # Layer 2: Block dangerous builtins in string
        for builtin in BLOCKED_BUILTINS:
            if f"{builtin}(" in code:
                return f"SECURITY: '{builtin}()' is blocked."

        # Layer 3: AST-level deep validation
        ast_error = _validate_ast(code)
        if ast_error:
            return ast_error

        return None

    def execute(
        self, code: str,
        df: Optional[pl.DataFrame] = None,
        dfs: Optional[Dict[str, pl.DataFrame]] = None,
        use_subprocess: bool = True,
    ) -> Dict[str, Any]:
        """
        Execute code with maximum security.
        
        Security layers:
        1. Preprocess (auto-correct)
        2. String-level blocklist
        3. AST-level validation
        4. Subprocess isolation (separate process, resource limits)
        5. Timeout (10s hard limit)
        6. Output cap (50KB)
        """
        # Auto-correct LLM hallucinations
        code = self._preprocess_code(code)

        # Security gate (string + AST)
        security_error = self._check_security(code)
        if security_error:
            return {"success": False, "output": "", "error": security_error}

        if use_subprocess:
            return self._execute_in_subprocess(code, df, dfs)
        else:
            return self._execute_inline(code, df, dfs)

    def _execute_in_subprocess(
        self, code: str,
        df: Optional[pl.DataFrame], dfs: Optional[Dict[str, pl.DataFrame]],
    ) -> Dict[str, Any]:
        """Execute in an isolated subprocess with resource limits."""
        # Serialize data to JSON for subprocess
        env_data = {}
        if df is not None:
            env_data["df"] = df.to_dicts()
        if dfs:
            env_data["dfs"] = {k: v.to_dicts() for k, v in dfs.items()}

        result_queue = multiprocessing.Queue()
        process = multiprocessing.Process(
            target=_worker,
            args=(code, json.dumps(env_data, default=str), result_queue),
        )
        process.start()
        process.join(timeout=EXEC_TIMEOUT_SECONDS)

        if process.is_alive():
            process.kill()
            process.join(timeout=2)
            return {
                "success": False,
                "output": "",
                "error": f"Code execution exceeded {EXEC_TIMEOUT_SECONDS}s limit (process killed)",
            }

        if result_queue.empty():
            return {
                "success": False,
                "output": "",
                "error": "Execution produced no result (process crashed or memory limit exceeded)",
            }

        return result_queue.get()

    def _execute_inline(
        self, code: str,
        df: Optional[pl.DataFrame], dfs: Optional[Dict[str, pl.DataFrame]],
    ) -> Dict[str, Any]:
        """Fallback: execute in-process (for testing or simple cases)."""
        safe_globals = {
            "pl": pl,
            "datetime": datetime,
            "math": math,
            "re": re,
            "collections": collections,
            "__builtins__": SAFE_BUILTINS,
        }
        locals_dict = {}
        if df is not None:
            locals_dict["df"] = df
        if dfs:
            locals_dict.update(dfs)
            locals_dict["dfs"] = dfs

        output_buffer = io.StringIO()
        old_stdout = sys.stdout
        sys.stdout = output_buffer

        try:
            old_handler = signal.signal(signal.SIGALRM, _timeout_handler)
            signal.alarm(EXEC_TIMEOUT_SECONDS)

            exec(code, safe_globals, locals_dict)

            signal.alarm(0)
            signal.signal(signal.SIGALRM, old_handler)

            output = output_buffer.getvalue()
            if len(output) > MAX_OUTPUT_BYTES:
                output = output[:MAX_OUTPUT_BYTES] + f"\n... [OUTPUT TRUNCATED]"

            return {"success": True, "output": output, "error": None}
        except TimeoutError as e:
            return {"success": False, "output": output_buffer.getvalue(), "error": str(e)}
        except Exception:
            return {"success": False, "output": output_buffer.getvalue(), "error": traceback.format_exc()}
        finally:
            sys.stdout = old_stdout
            output_buffer.close()
            try:
                signal.alarm(0)
            except Exception:
                pass
