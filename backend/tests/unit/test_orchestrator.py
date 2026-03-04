import pytest
import os
from modules.data.orchestrator import DataOrchestrator
from modules.data.duckdb_provider import DuckDBDataProvider

class TestDataOrchestrator:
    @pytest.fixture
    def session_id(self):
        return "test_session_abc"

    def test_initialization_duckdb(self, session_id):
        orchestrator = DataOrchestrator(session_id=session_id, use_db=True)
        assert isinstance(orchestrator.provider, DuckDBDataProvider)
        assert f"{session_id}.duckdb" in orchestrator.provider.db_path
        orchestrator.cleanup()

    def test_ingest_and_schema_summary(self, session_id, temp_csv_file):
        orchestrator = DataOrchestrator(session_id=session_id)
        orchestrator.ingest_files([temp_csv_file])
        
        summary = orchestrator.get_schema_summary()
        assert "AVAILABLE DATABASE TABLES" in summary
        # Table name is derived from filename
        table_name = os.path.splitext(os.path.basename(temp_csv_file))[0]
        assert table_name in summary
        orchestrator.cleanup()

    def test_cleanup_removes_db_file(self, session_id):
        orchestrator = DataOrchestrator(session_id=session_id)
        db_path = orchestrator.provider.db_path
        orchestrator.cleanup()
        assert not os.path.exists(db_path)

    def test_session_isolation(self, temp_csv_file):
        # Session 1
        s1 = DataOrchestrator(session_id="session_1")
        s1.ingest_files([temp_csv_file])
        
        # Session 2
        s2 = DataOrchestrator(session_id="session_2")
        # s2 should NOT see s1's tables
        schema2 = s2.provider.get_schema()
        assert len(schema2) == 0
        
        s1.cleanup()
        s2.cleanup()
