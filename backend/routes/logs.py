from fastapi import APIRouter, HTTPException
from datetime import datetime
from pathlib import Path
import sys

router = APIRouter(tags=["Logs"])


def get_app_root():
    """
    Returns the writable application directory.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent

    return Path(__file__).resolve().parents[2]


@router.get("/logs")
async def get_logs():
    app_root = get_app_root()
    log_path = app_root / "Output" / "Logs" / "app.log"

    if not log_path.exists():
        return {
            "success": True,
            "message": "Log file empty.",
            "data": "",
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }

    try:
        with open(log_path, "r", encoding="utf-8") as f:
            lines = f.readlines()

        last_lines = "".join(lines[-200:])

        return {
            "success": True,
            "message": "Fetched recent logs.",
            "data": last_lines,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )