import os
import shutil
import sys
from pathlib import Path

# Add backend to path so we can import config
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from config import settings

def migrate():
    print("🚀 Starting storage migration...")
    
    storage_dir = settings.STORAGE_DIR
    datasets_dir = settings.DATASETS_DIR
    reports_dir = settings.REPORTS_DIR
    metadata_dir = settings.METADATA_DIR
    temp_db_dir = settings.TEMP_DB_DIR
    
    # Extensions mapping
    DATA_EXTS = {".csv", ".xlsx", ".xls", ".parquet"}
    REPORT_EXTS = {".pdf", ".typ"}
    
    if not storage_dir.exists():
        print("❌ Storage directory not found. Nothing to migrate.")
        return

    # Create sub-dirs if they don't exist
    for d in [datasets_dir, reports_dir, metadata_dir, temp_db_dir]:
        d.mkdir(parents=True, exist_ok=True)

    moved_count = 0
    
    for item in storage_dir.iterdir():
        if not item.is_file():
            # Handle special case: temp_dbs directory
            if item.name == "temp_dbs" and item.is_dir():
                print(f"📦 Moving temp_dbs directory content...")
                for db_file in item.iterdir():
                    if db_file.is_file():
                        target = temp_db_dir / db_file.name
                        shutil.move(str(db_file), str(target))
                        print(f"  ✅ Moved {db_file.name} -> temp_dbs/")
                continue
            continue
            
        filename = item.name
        ext = item.suffix.lower()
        
        target_path = None
        
        # 1. Handle Metadata files (.metadata.json)
        if filename.endswith(".metadata.json"):
            target_path = metadata_dir / filename
        # 2. Handle Data files
        elif ext in DATA_EXTS:
            target_path = datasets_dir / filename
        # 3. Handle Reports
        elif ext in REPORT_EXTS:
            target_path = reports_dir / filename
            
        if target_path:
            try:
                shutil.move(str(item), str(target_path))
                print(f"✅ Moved {filename} -> {target_path.parent.name}/")
                moved_count += 1
            except Exception as e:
                print(f"❌ Failed to move {filename}: {e}")

    print(f"\n✨ Migration complete! Total files moved: {moved_count}")

if __name__ == "__main__":
    migrate()
