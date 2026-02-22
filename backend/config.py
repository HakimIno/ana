from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Optional

class Settings(BaseSettings):
    """Application settings and environment variables."""
    
    # Project Info
    PROJECT_NAME: str = "AI Business Analyst Assistant"
    VERSION: str = "0.1.0"
    
    # API Keys
    OPENAI_API_KEY: Optional[str] = None
    
    # Storage Paths
    BASE_DIR: Path = Path(__file__).resolve().parent
    STORAGE_DIR: Path = BASE_DIR / "uploads"
    QDRANT_PATH: Path = BASE_DIR / "qdrant_db"
    
    # RAG Settings
    QDRANT_COLLECTION_NAME: str = "business_data"
    EMBEDDING_MODEL: str = "text-embedding-3-small"
    
    # Model configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore"
    )

settings = Settings()

# Ensure directories exist
settings.STORAGE_DIR.mkdir(parents=True, exist_ok=True)
settings.QDRANT_PATH.mkdir(parents=True, exist_ok=True)
