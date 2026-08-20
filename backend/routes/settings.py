from fastapi import APIRouter, HTTPException
from datetime import datetime
from backend.services.settings_service import settings_service
from backend.models.settings import SettingsModel

router = APIRouter(tags=["Settings"])

@router.get("/settings")
async def get_settings():
    try:
        settings = await settings_service.get_settings()
        return {
            "success": True,
            "message": "Fetched settings.",
            "data": settings.model_dump(),
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/settings")
async def save_settings(settings: SettingsModel):
    try:
        success = await settings_service.save_settings(settings)
        return {
            "success": success,
            "message": "Settings updated successfully.",
            "data": settings.model_dump(),
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
