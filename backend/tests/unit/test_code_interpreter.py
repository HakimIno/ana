import pytest
import polars as pl
from modules.llm.code_interpreter import CodeInterpreter, _validate_ast


class TestCodeInterpreter:
    """Tests for hardened CodeInterpreter: corrections, security, and execution."""

    @pytest.fixture
    def interpreter(self):
        return CodeInterpreter()

    # ─────────────────────────────────────────────
    # _preprocess_code
    # ─────────────────────────────────────────────

    def test_groupby_correction(self, interpreter):
        code = "df.groupby('Branch').agg(pl.col('Revenue').sum())"
        result = interpreter._preprocess_code(code)
        assert ".group_by(" in result
        assert ".groupby(" not in result

    def test_first_correction(self, interpreter):
        code = "df.first()"
        result = interpreter._preprocess_code(code)
        assert ".head(1)" in result

    def test_fillna_correction(self, interpreter):
        code = "df.fillna(0)"
        result = interpreter._preprocess_code(code)
        assert ".fill_null(0)" in result

    def test_isnull_correction(self, interpreter):
        code = "df.select(pl.col('x').isnull())"
        result = interpreter._preprocess_code(code)
        assert ".is_null()" in result

    def test_pandas_import_blocked(self, interpreter):
        code = "import pandas as pd\npd.DataFrame({'a': [1]})"
        result = interpreter._preprocess_code(code)
        assert "pandas not available" in result

    def test_rename_columns_fix(self, interpreter):
        code = 'df.rename(columns={"old": "new"})'
        result = interpreter._preprocess_code(code)
        assert "columns=" not in result
        assert '.rename({"old": "new"})' in result

    # ─────────────────────────────────────────────
    # _check_security (string + AST)
    # ─────────────────────────────────────────────

    def test_blocks_os_import(self, interpreter):
        assert interpreter._check_security("import os") is not None

    def test_blocks_subprocess(self, interpreter):
        assert interpreter._check_security("import subprocess") is not None

    def test_blocks_eval(self, interpreter):
        assert interpreter._check_security("eval('1+1')") is not None

    def test_blocks_exec(self, interpreter):
        assert interpreter._check_security("exec('print(1)')") is not None

    def test_blocks_open(self, interpreter):
        assert interpreter._check_security("open('/etc/passwd')") is not None

    def test_blocks_dunder(self, interpreter):
        assert interpreter._check_security("x.__class__.__subclasses__()") is not None

    def test_blocks_import_builtin(self, interpreter):
        assert interpreter._check_security("__import__('os')") is not None

    def test_allows_polars(self, interpreter):
        assert interpreter._check_security("result = pl.col('x').sum()") is None

    def test_allows_print(self, interpreter):
        assert interpreter._check_security("print('hello')") is None

    def test_allows_basic_python(self, interpreter):
        assert interpreter._check_security("x = [1, 2, 3]\nprint(sum(x))") is None

    # ─────────────────────────────────────────────
    # AST Validator directly
    # ─────────────────────────────────────────────

    def test_ast_blocks_ctypes(self):
        assert _validate_ast("import ctypes") is not None

    def test_ast_blocks_pickle(self):
        assert _validate_ast("import pickle") is not None

    def test_ast_blocks_dunder_subclass(self):
        assert _validate_ast("x.__class__.__subclasses__()") is not None

    def test_ast_allows_normal_code(self):
        assert _validate_ast("x = 1 + 2\nprint(x)") is None

    # ─────────────────────────────────────────────
    # execute (using inline mode for test speed)
    # ─────────────────────────────────────────────

    def test_execute_simple_print(self, interpreter):
        result = interpreter.execute("print('hello world')", use_subprocess=False)
        assert result["success"] is True
        assert "hello world" in result["output"]

    def test_execute_with_df(self, interpreter):
        df = pl.DataFrame({"A": [1, 2, 3], "B": [4, 5, 6]})
        result = interpreter.execute("print(df.shape)", df=df, use_subprocess=False)
        assert result["success"] is True
        assert "(3, 2)" in result["output"]

    def test_execute_with_dfs(self, interpreter):
        dfs = {
            "sales": pl.DataFrame({"Revenue": [100, 200]}),
            "costs": pl.DataFrame({"Cost": [50, 80]}),
        }
        result = interpreter.execute("print(sales.shape, costs.shape)", dfs=dfs, use_subprocess=False)
        assert result["success"] is True

    def test_execute_syntax_error(self, interpreter):
        result = interpreter.execute("if True print('x')", use_subprocess=False)
        assert result["success"] is False
        assert result["error"] is not None

    def test_execute_blocked_import(self, interpreter):
        result = interpreter.execute("import os\nos.listdir('.')", use_subprocess=False)
        assert result["success"] is False
        assert "SECURITY" in result["error"]

    def test_execute_blocked_eval(self, interpreter):
        result = interpreter.execute("x = eval('1+1')", use_subprocess=False)
        assert result["success"] is False
        assert "SECURITY" in result["error"]

    def test_execute_polars_groupby_autocorrect(self, interpreter):
        df = pl.DataFrame({"Branch": ["A", "B", "A"], "Revenue": [100, 200, 150]})
        code = "result = df.groupby('Branch').agg(pl.col('Revenue').sum())\nprint(result.shape)"
        result = interpreter.execute(code, df=df, use_subprocess=False)
        assert result["success"] is True

    # ─────────────────────────────────────────────
    # Subprocess mode
    # ─────────────────────────────────────────────

    def test_subprocess_simple(self, interpreter):
        result = interpreter.execute("print('subprocess ok')", use_subprocess=True)
        assert result["success"] is True
        assert "subprocess ok" in result["output"]

    def test_subprocess_with_df(self, interpreter):
        df = pl.DataFrame({"X": [10, 20, 30]})
        result = interpreter.execute("print(df['X'].sum())", df=df, use_subprocess=True)
        assert result["success"] is True
        assert "60" in result["output"]
