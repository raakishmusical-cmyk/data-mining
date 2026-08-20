from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from datetime import datetime
from backend.database.sqlite import db

router = APIRouter(tags=["Keywords"])

class KeywordAddRequest(BaseModel):
    keyword: str

@router.get("/keywords")
async def get_keywords():
    try:
        rows = await db.execute("SELECT * FROM keywords ORDER BY is_default DESC, keyword ASC")
        return {
            "success": True,
            "message": "Fetched keywords list.",
            "data": rows,
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/keywords")
async def add_keyword(req: KeywordAddRequest):
    kw = req.keyword.strip()
    if not kw:
        raise HTTPException(status_code=400, detail="Keyword cannot be empty.")
        
    try:
        # Check if already exists
        exists = await db.execute("SELECT id FROM keywords WHERE lower(keyword) = ?", (kw.lower(),))
        if exists:
            raise HTTPException(status_code=400, detail="Keyword already exists.")
            
        last_id = await db.execute("INSERT INTO keywords (keyword, is_default) VALUES (?, 0)", (kw,))
        return {
            "success": True,
            "message": f"Keyword '{kw}' added successfully.",
            "data": {
                "id": last_id,
                "keyword": kw,
                "is_default": 0
            },
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/keywords/{id}")
async def delete_keyword(id: int):
    try:
        # Check if exists and is not default
        row = await db.execute("SELECT is_default FROM keywords WHERE id = ?", (id,))
        if not row:
            raise HTTPException(status_code=404, detail="Keyword not found.")
            
        if row[0]["is_default"] == 1:
            raise HTTPException(status_code=400, detail="Cannot delete default system keywords.")
            
        await db.execute("DELETE FROM keywords WHERE id = ?", (id,))
        return {
            "success": True,
            "message": "Keyword deleted successfully.",
            "data": {},
            "errors": [],
            "timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
