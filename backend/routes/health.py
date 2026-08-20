from fastapi import APIRouter
from datetime import datetime

router = APIRouter(tags=["Health"])

@router.get("/health")
async def health_check():
    return {
        "success": True,
        "message": "Backend status: Healthy",
        "data": {
            "status": "ready",
            "time": datetime.now().isoformat()
        },
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }
