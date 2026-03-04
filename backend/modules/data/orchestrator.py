from typing import Dict, List, Any, Optional
from .base_provider import BaseDataProvider
from .csv_provider import CSVDataProvider
from .duckdb_provider import DuckDBDataProvider
import os
import logging

logger = logging.getLogger(__name__)

class DataOrchestrator:
    """
    Orchestrator to manage different Data Providers.
    Decides between CSV and DuckDB based on data size and session settings.
    """

    def __init__(self, session_id: str, use_db: bool = True):
        self.session_id = session_id
        self.use_db = use_db
        self.provider: BaseDataProvider = None
        self._initialize_provider()

    def _initialize_provider(self):
        if self.use_db:
            # Create a per-session DuckDB file for isolation
            from config import settings
            db_dir = settings.TEMP_DB_DIR
            db_path = os.path.join(db_dir, f"{self.session_id}.duckdb")
            self.provider = DuckDBDataProvider(db_path=db_path)
            logger.info(f"Initialized DuckDB provider for session {self.session_id}")
        else:
            self.provider = CSVDataProvider()
            logger.info(f"Initialized CSV provider for session {self.session_id}")

    def ingest_files(self, file_paths: List[str]):
        """
        Load multiple files into the active provider.
        """
        for path in file_paths:
            if os.path.exists(path):
                success = self.provider.load_file(path)
                if success:
                    logger.info(f"Successfully ingested {path}")
                else:
                    logger.warning(f"Failed to ingest {path}")

    def query(self, sql: str) -> Any:
        return self.provider.query(sql)

    def disconnect(self):
        if self.provider:
            self.provider.disconnect()

    def reconnect(self):
        if self.provider:
            self.provider.reconnect()

    def get_schema_summary(self) -> str:
        """
        Returns a formatted string describing the available tables and columns.
        This is injected into the LLM prompt.
        """
        schema = self.provider.get_schema()
        if not schema:
            return "No data tables available."
        
        summary = ["AVAILABLE DATABASE TABLES:"]
        for table, cols in schema.items():
            summary.append(f"- Table: `{table}` | Columns: {', '.join(cols)}")
        return "\n".join(summary)

    def cleanup(self):
        """
        Clean up the session-based data.
        """
        if self.provider:
            self.provider.close()
            logger.info(f"Cleaned up data provider for session {self.session_id}")
