import json
import logging
from pathlib import Path
from typing import Dict, Optional, List
from config import settings

logger = logging.getLogger(__name__)

class MetadataManager:
    """Manages business-to-technical mapping for spreadsheet columns."""

    def __init__(self, storage_dir: Path = settings.STORAGE_DIR):
        self.storage_dir = Path(storage_dir)
        self.storage_dir.mkdir(parents=True, exist_ok=True)

    def _get_metadata_path(self, filename: str) -> Path:
        return self.storage_dir / f"{filename}.metadata.json"

    def get_dictionary(self, filename: str) -> Dict[str, str]:
        """Retrieves the business term mapping for a file."""
        path = self._get_metadata_path(filename)
        if not path.exists():
            return {}
        try:
            with open(path, "r", encoding="utf-8") as f:
                return json.load(f).get("dictionary", {})
        except Exception as e:
            logger.error(f"Error reading metadata for {filename}: {e}")
            return {}

    def save_dictionary(self, filename: str, dictionary: Dict[str, str]):
        """Saves a business term mapping for a file."""
        path = self._get_metadata_path(filename)
        try:
            metadata = {}
            if path.exists():
                with open(path, "r", encoding="utf-8") as f:
                    metadata = json.load(f)
            
            metadata["dictionary"] = dictionary
            with open(path, "w", encoding="utf-8") as f:
                json.dump(metadata, f, indent=2, ensure_ascii=False)
            logger.info(f"Saved metadata dictionary for {filename}")
        except Exception as e:
            logger.error(f"Error saving metadata for {filename}: {e}")

    def generate_default_dictionary(self, filename: str, columns: List[str]):
        """Generates a default business dictionary based on common column naming patterns."""
        mapping = {}
        for col in columns:
            # Simple heuristic mapping
            clean = col.replace("_", " ").title()
            mapping[col] = clean
            
        self.save_dictionary(filename, mapping)
        return mapping
