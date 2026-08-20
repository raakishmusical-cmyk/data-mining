import os
from backend.repositories.history_repository import history_repo

class DownloadService:
    async def get_download_path(self, download_id: str) -> str:
        """Resolves file ID and returns the physical path for streaming download, checking all candidate folders."""
        entry = await history_repo.get_entry_by_id(download_id)
        if not entry:
            return ""
            
        file_name = entry["file_name"]
        
        # Check multiple potential folders for physical file existence
        candidates = [
            os.path.join("Output", file_name),
            os.path.join("Output/Mining", file_name),
            os.path.join("Output/Marked", file_name),
            os.path.join("Output/Cleaned", file_name),
            os.path.join("Output/Validation", file_name)
        ]
        
        for cand in candidates:
            if os.path.exists(cand):
                return cand
                
        return ""

download_service = DownloadService()
