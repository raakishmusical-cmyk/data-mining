from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
import os
from backend.services.download_service import download_service

router = APIRouter(tags=["Downloads"])

@router.get("/download/{download_id}")
async def download_file(download_id: str):
    filepath = await download_service.get_download_path(download_id)
    if not filepath or not os.path.exists(filepath):
        raise HTTPException(status_code=404, detail="Requested file not found or has been deleted.")
        
    return FileResponse(
        path=filepath,
        filename=os.path.basename(filepath),
        media_type="application/octet-stream"
    )
