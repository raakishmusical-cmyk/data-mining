import os
from datetime import datetime
from backend.repositories.history_repository import history_repo
from backend.repositories.file_repository import file_repo
from backend.models.history import HistoryItemModel
from backend.utils.logger import logger

class HistoryService:
    async def get_recent_files(self) -> list[dict]:
        """Returns list of files, automatically scanning Output directories to sync-register missing physical files, and checks candidates to prevent pruning."""
        # 1. Query current registered records
        raw_entries = await history_repo.get_all_entries()
        registered_names = {entry["file_name"] for entry in raw_entries}
        
        # 2. Auto-scan Output directories to sync existing files on disk
        scan_dirs = {
            "Output": "Mining Files",
            "Output/Mining": "Mining Files",
            "Output/Marked": "Marked Files",
            "Output/Cleaned": "Cleaned Files",
            "Output/Validation": "Processed Files"
        }
        
        for s_dir, cat in scan_dirs.items():
            if not os.path.exists(s_dir):
                continue
            for fname in os.listdir(s_dir):
                fpath = os.path.join(s_dir, fname)
                if os.path.isdir(fpath):
                    continue
                if not (fname.endswith(".xlsx") or fname.endswith(".zip")):
                    continue
                if fname in registered_names:
                    continue
                
                # Try parsing district from filename, e.g. Salem_10_keywords_...
                parts = fname.split("_")
                district = parts[0] if len(parts) >= 1 else "Unknown"
                if district.lower() in ("processed", "clean", "mining"):
                    district = parts[1] if len(parts) >= 2 else "Validation"
                
                # Rows counting
                row_count = 0
                try:
                    import pandas as pd
                    if fname.endswith(".csv"):
                        df = pd.read_csv(fpath)
                    else:
                        df = pd.read_excel(fpath)
                    row_count = len(df)
                except Exception:
                    pass
                    
                # Register in database history
                await self.register_file(
                    filename=fname,
                    category=cat,
                    district=district,
                    keyword_count=0,
                    row_count=row_count,
                    filepath=fpath
                )
                registered_names.add(fname)
                
        # 3. Reload entries after sync scanner runs
        raw_entries = await history_repo.get_all_entries()
        active_files = []
        
        for entry in raw_entries:
            file_name = entry["file_name"]
            if file_name.endswith(".csv"):
                continue
            
            # Check multiple potential folders for physical file existence
            candidates = [
                os.path.join("Output", file_name),
                os.path.join("Output/Mining", file_name),
                os.path.join("Output/Marked", file_name),
                os.path.join("Output/Cleaned", file_name),
                os.path.join("Output/Validation", file_name)
            ]
            
            filepath = None
            for cand in candidates:
                if os.path.exists(cand):
                    filepath = cand
                    break
            
            # Prune entry if physical file is missing from disk
            if filepath is None:
                logger.info(f"File {file_name} missing from disk. Automatically pruning history database record.")
                await history_repo.delete_entry(entry["file_id"])
            else:
                # Update file size dynamically in case it changed
                size_formatted = file_repo.get_file_size_formatted(filepath)
                entry_dict = dict(entry)
                entry_dict["file_size"] = size_formatted
                active_files.append(entry_dict)
                
        return active_files

    async def register_file(self, filename: str, category: str, district: str, keyword_count: int, row_count: int, filepath: str) -> str:
        """Saves a generated file inside the SQLite history catalog."""
        import uuid
        file_id = str(uuid.uuid4())
        created_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        size_formatted = file_repo.get_file_size_formatted(filepath)
        
        item = HistoryItemModel(
            file_id=file_id,
            file_name=filename,
            category=category,
            district=district,
            keyword_count=keyword_count,
            row_count=row_count,
            file_size=size_formatted,
            created_at=created_time,
            status="ready"
        )
        
        await history_repo.add_entry(item)
        logger.info(f"Registered file history entry: {filename} under ID: {file_id}")
        return file_id

    async def delete_file(self, file_id: str) -> bool:
        """Deletes file physically from disk and removes history reference."""
        entry = await history_repo.get_entry_by_id(file_id)
        if not entry:
            return False
            
        file_name = entry["file_name"]
        
        # Check candidate locations to delete
        candidates = [
            os.path.join("Output", file_name),
            os.path.join("Output/Mining", file_name),
            os.path.join("Output/Marked", file_name),
            os.path.join("Output/Cleaned", file_name),
            os.path.join("Output/Validation", file_name)
        ]
        
        filepath = None
        for cand in candidates:
            if os.path.exists(cand):
                filepath = cand
                break
                
        if filepath is None:
            filepath = os.path.join("Output/Mining", file_name) # default fallback
            
        # Delete from disk
        file_repo.delete_file(filepath)
        
        # Delete from database
        await history_repo.delete_entry(file_id)
        return True

history_service = HistoryService()
