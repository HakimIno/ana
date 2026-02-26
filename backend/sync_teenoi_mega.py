import polars as pl
from pathlib import Path
from modules.storage.metadata_manager import MetadataManager
from config import settings

def sync_teenoi_metadata():
    meta_manager = MetadataManager()
    uploads_dir = Path(settings.STORAGE_DIR)
    
    # Files we want to group under "Teenoi Mega"
    teenoi_files = ["sales.csv", "staff.csv", "feedback.csv", "branches.csv", "inventory.csv", "promotions.csv"]
    
    print(f"Syncing Teenoi Mega metadata...")
    
    for filename in teenoi_files:
        csv_path = uploads_dir / filename
        if not csv_path.exists():
            print(f"  - Skip: {filename} (not found)")
            continue
            
        try:
            df = pl.read_csv(csv_path, n_rows=1)
            columns = df.columns
            
            # Generate default dictionary
            meta_manager.generate_default_dictionary(filename, columns)
            
            # Force set group to "Teenoi Mega"
            meta_manager.save_group(filename, "Teenoi Mega")
            
            print(f"  - Synced & Grouped: {filename}")
        except Exception as e:
            print(f"  - Error syncing {filename}: {e}")

if __name__ == "__main__":
    sync_teenoi_metadata()
