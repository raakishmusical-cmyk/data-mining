from fastapi import APIRouter, WebSocket, WebSocketDisconnect, HTTPException
from pydantic import BaseModel
from typing import List
from datetime import datetime
from backend.services.mining_service import mining_service

router = APIRouter(tags=["Mining"])

class StartMiningRequest(BaseModel):
    country: str
    state: str
    districts: List[str]
    keywords: List[str]
    format: str = "xlsx"
    translate_to_english: bool = True

@router.get("/mining/checkpoint")
async def get_active_checkpoint():
    try:
        checkpoint = await mining_service.get_active_checkpoint()
        return {
            "success": True,
            "message": "Fetched active checkpoint if exists.",
            "data": checkpoint,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/mining/start")
async def start_mining(req: StartMiningRequest):
    if req.country not in ("USA"):
        raise HTTPException(status_code=400, detail="Country must be USA.")
    success, msg = await mining_service.start_job(
        req.country, req.state, req.districts, req.keywords, req.format, req.translate_to_english
    )
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "data": {},
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/mining/pause")
async def pause_mining():
    success, msg = await mining_service.pause_job()
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "data": {},
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/mining/resume")
async def resume_mining():
    success, msg = await mining_service.resume_job()
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "data": {},
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }

@router.post("/mining/stop")
async def stop_mining():
    success, msg = await mining_service.stop_job()
    if not success:
        raise HTTPException(status_code=400, detail=msg)
    return {
        "success": True,
        "message": msg,
        "data": {},
        "errors": [],
        "timestamp": datetime.now().isoformat()
    }

@router.websocket("/ws/mining")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    mining_service.register_websocket(websocket)
    # Broadcast initial state immediately
    await mining_service.broadcast_status()
    try:
        while True:
            # Keep connection alive; ignore any client input messages
            data = await websocket.receive_text()
    except WebSocketDisconnect:
        mining_service.unregister_websocket(websocket)
