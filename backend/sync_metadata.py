import polars as pl
from pathlib import Path
from modules.storage.metadata_manager import MetadataManager
from config import settings

def sync_all_metadata():
    meta_manager = MetadataManager()
    uploads_dir = Path(settings.STORAGE_DIR)
    
    csv_files = list(uploads_dir.glob("*.csv"))
    print(f"Syncing metadata for {len(csv_files)} files...")
    
    for csv_file in csv_files:
        try:
            df = pl.read_csv(csv_file, n_rows=1)
            columns = df.columns
            meta_manager.generate_default_dictionary(csv_file.name, columns)
            print(f"  - Synced: {csv_file.name}")
        except Exception as e:
            print(f"  - Error syncing {csv_file.name}: {e}")

if __name__ == "__main__":
    sync_all_metadata()
