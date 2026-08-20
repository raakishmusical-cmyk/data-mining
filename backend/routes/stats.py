from fastapi import APIRouter
from datetime import datetime
from backend.services.mining_service import mining_service

router = APIRouter(tags=["Statistics"])

@router.get("/statistics")
async def get_statistics():
    return {
        "success": True,
        "message": "Fetched live statistics.",
        "data": mining_service.stats,
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }
