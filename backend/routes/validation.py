from fastapi import APIRouter, UploadFile, File, HTTPException
from pydantic import BaseModel
from datetime import datetime
from backend.services.validation_service import validation_service

router = APIRouter(tags=["Validation"])

class SessionRequest(BaseModel):
    session_id: str
    delete_row_numbers: list[int] = None

@router.post("/validation/upload")
async def upload_file(file: UploadFile = File(...)):
    try:
        content = await file.read()
        session_id = await validation_service.create_session(file.filename, content)
        row_count = validation_service.sessions[session_id]["row_count"]
        return {
            "success": True,
            "message": "File uploaded successfully.",
            "data": {
                "session_id": session_id,
                "file_name": file.filename,
                "row_count": row_count
            },
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Upload failed: {str(e)}")

@router.post("/validation/find-duplicates")
async def find_duplicates(req: SessionRequest):
    try:
        results = await validation_service.scan_duplicates(req.session_id)
        return {
            "success": True,
            "message": "Scanned duplicate records.",
            "data": results,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validation/mark")
async def mark_duplicates(req: SessionRequest):
    try:
        file_id = await validation_service.mark_duplicates(req.session_id)
        return {
            "success": True,
            "message": "Generated marked spreadsheet successfully.",
            "data": {
                "file_id": file_id
            },
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validation/delete")
async def delete_duplicates(req: SessionRequest):
    try:
        file_id = await validation_service.delete_duplicates(req.session_id, req.delete_row_numbers)
        return {
            "success": True,
            "message": "Generated cleaned duplicate-free spreadsheet.",
            "data": {
                "file_id": file_id
            },
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/validation/fix-classification")
async def fix_classification(req: SessionRequest):
    try:
        file_id = await validation_service.fix_industry_and_tags(req.session_id)
        return {
            "success": True,
            "message": "Updated industries and tags.",
            "data": {
                "file_id": file_id
            },
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except ValueError as ve:
        raise HTTPException(status_code=400, detail=str(ve))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
