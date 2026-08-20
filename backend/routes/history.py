from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.services.history_service import history_service

router = APIRouter(tags=["History"])

@router.get("/history")
async def get_history():
    try:
        files = await history_service.get_recent_files()
        return {
            "success": True,
            "message": "Fetched history list.",
            "data": files,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/history/{file_id}")
async def delete_history_item(file_id: str):
    try:
        success = await history_service.delete_file(file_id)
        if not success:
            raise HTTPException(status_code=404, detail="File entry not found.")
        return {
            "success": True,
            "message": "File and history entry deleted successfully.",
            "data": {},
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
