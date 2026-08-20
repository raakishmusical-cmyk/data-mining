import os
from pathlib import Path
from backend.utils.logger import logger

class FileRepository:
    def __init__(self, root_dir: str = "."):
        self.root_path = Path(root_dir).resolve()
        
    def ensure_directories(self):
        """Creates the required production folder structure."""
        dirs = [
            "Output/Mining",
            "Output/Validation",
            "Output/Marked",
            "Output/Cleaned",
            "Output/Logs",
            "Output/Database",
            "Output/Temp"
        ]
        for d in dirs:
            path = self.root_path / d
            path.mkdir(parents=True, exist_ok=True)
            
    def secure_path(self, relative_path: str) -> Path:
        """Resolves path and checks for path traversal vulnerabilities."""
        target_path = Path(relative_path).resolve()
        if not str(target_path).startswith(str(self.root_path)):
            raise PermissionError("Path traversal attempt detected.")
        return target_path

    def get_file_size_formatted(self, filepath: str) -> str:
        """Returns size of a file in standard human-readable format."""
        try:
            path = self.secure_path(filepath)
            if not path.exists():
                return "0 B"
            size_bytes = path.stat().st_size
            if size_bytes == 0:
                return "0 B"
            size_name = ("B", "KB", "MB", "GB")
            import math
            i = int(math.floor(math.log(size_bytes, 1024)))
            p = math.pow(1024, i)
            s = round(size_bytes / p, 2)
            return f"{s} {size_name[i]}"
        except Exception as e:
            logger.error(f"Error determining file size: {e}")
            return "N/A"
            
    def delete_file(self, filepath: str) -> bool:
        """Deletes a physical file securely."""
        try:
            path = self.secure_path(filepath)
            if path.exists():
                path.unlink()
                logger.info(f"File deleted successfully: {filepath}")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete file {filepath}: {e}")
            raise e

file_repo = FileRepository()
