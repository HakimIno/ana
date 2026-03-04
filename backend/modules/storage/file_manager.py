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
        self.datasets_dir = settings.DATASETS_DIR
        self.reports_dir = settings.REPORTS_DIR
        
        # Ensure sub-dirs exist
        self.storage_dir.mkdir(parents=True, exist_ok=True)
        self.datasets_dir.mkdir(parents=True, exist_ok=True)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def save_file(self, file_content: bytes, filename: str) -> Path:
        """Save a file to the appropriate sub-directory."""
        target_dir = self.get_directory_by_extension(filename)
        file_path = target_dir / filename
        try:
            with open(file_path, "wb") as f:
                f.write(file_content)
            logger.info(f"File saved to {target_dir.name}: {file_path}")
            return file_path
        except Exception as e:
            logger.error(f"Error saving file {filename}: {e}")
            raise IOError(f"Failed to save file: {e}")

    def get_directory_by_extension(self, filename: str) -> Path:
        """Helper to route files based on extension."""
        ext = Path(filename).suffix.lower()
        if ext in {".csv", ".xlsx", ".xls", ".parquet"}:
            return self.datasets_dir
        elif ext in {".pdf", ".typ"}:
            return self.reports_dir
        return self.storage_dir

    def get_file_path(self, filename: str) -> Path:
        """Get the absolute path of a stored file, searching sub-dirs if needed."""
        # 1. Try root
        file_path = self.storage_dir / filename
        if file_path.exists(): return file_path
        
        # 2. Try datasets
        file_path = self.datasets_dir / filename
        if file_path.exists(): return file_path
        
        # 3. Try reports
        file_path = self.reports_dir / filename
        if file_path.exists(): return file_path
        
        raise FileNotFoundError(f"File not found: {filename}")

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

    def list_files(self, file_type: str = "any") -> List[Dict[str, Any]]:
        """List stored files with metadata across sub-directories."""
        files = []
        supported_data = {".csv", ".xlsx", ".xls", ".parquet"}
        supported_reports = {".pdf", ".typ"}
        
        # Search targets
        search_dirs = [self.storage_dir, self.datasets_dir, self.reports_dir]
        
        for s_dir in search_dirs:
            if not s_dir.exists(): continue
            for file_path in s_dir.iterdir():
                if not file_path.is_file(): continue
                
                ext = file_path.suffix.lower()
                
                # Filtering logic
                is_data = ext in supported_data
                is_report = ext in supported_reports
                
                if file_type == "data" and not is_data: continue
                if file_type == "report" and not is_report: continue
                if file_type == "any" and not (is_data or is_report): continue
                
                stats = file_path.stat()
                files.append({
                    "filename": file_path.name,
                    "size": stats.st_size,
                    "created_at": stats.st_ctime,
                    "path": str(file_path),
                    "type": "data" if is_data else "report"
                })
        
        # Deduplicate by filename (pick first found)
        seen = set()
        unique_files = []
        for f in files:
            if f["filename"] not in seen:
                unique_files.append(f)
                seen.add(f["filename"])
                
        return sorted(unique_files, key=lambda x: x["created_at"], reverse=True)

    def cleanup(self):
        """Clean up the entire storage directory."""
        try:
            shutil.rmtree(self.storage_dir)
            self.storage_dir.mkdir(parents=True, exist_ok=True)
            logger.info("Storage directory cleaned up.")
        except Exception as e:
            logger.error(f"Error cleaning up storage: {e}")
            raise IOError(f"Failed to cleanup storage: {e}")
