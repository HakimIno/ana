import shutil
import os
from pathlib import Path
from typing import List, Dict, Any
from config import settings
import logging

logger = logging.getLogger(__name__)

class FileManager:
    """Manager for file uploads, storage, and metadata."""

    def __init__(self, storage_dir: Path = settings.STORAGE_DIR):
        self.storage_dir = storage_dir
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: bytes, filename: str) -> Path:
        """Save a file to the storage directory."""
        file_path = self.storage_dir / filename
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File saved: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise IOError(f"Failed to save file: {e}")

    def get_file_path(self, filename: str) -> Path:
        """Get the absolute path of a stored file."""
        file_path = self.storage_dir / filename
        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {filename}")
        return file_path

    def delete_file(self, filename: str) -> bool:
        """Delete a file from the storage directory."""
        try:
            file_path = self.get_file_path(filename)
            file_path.unlink()
            logger.info(f"File deleted: {filename}")
            return True
        except FileNotFoundError:
            return False
        except Exception as e:
            logger.error(f"Error deleting file {filename}: {e}")
            raise IOError(f"Failed to delete file: {e}")

    def list_files(self) -> List[Dict[str, Any]]:
        """List all stored files with metadata."""
        files = []
        for file_path in self.storage_dir.iterdir():
            if file_path.is_file():
                stats = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stats.st_size,
                    "created_at": stats.st_ctime,
                    "path": str(file_path)
                })
        return files

    def cleanup(self):
        """Clean up the entire storage directory."""
        try:
            shutil.rmtree(self.storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Storage directory cleaned up.")
        except Exception as e:
            logger.error(f"Error cleaning up storage: {e}")
            raise IOError(f"Failed to cleanup storage: {e}")
