from backend.database.sqlite import db
from backend.models.history import HistoryItemModel
from typing import List, Optional

class HistoryRepository:
    async def add_entry(self, item: HistoryItemModel) -> int:
        query = """
        INSERT INTO history (file_id, file_name, category, district, keyword_count, row_count, file_size, created_at, status)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        params = (
            item.file_id, item.file_name, item.category, item.district,
            item.keyword_count, item.row_count, item.file_size, item.created_at, item.status
        )
        return await db.execute(query, params)
        
    async def get_all_entries(self, category: Optional[str] = None) -> List[dict]:
        if category:
            query = "SELECT * FROM history WHERE category = ? ORDER BY id DESC"
            return await db.execute(query, (category,))
        else:
            query = "SELECT * FROM history ORDER BY id DESC"
            return await db.execute(query)
            
    async def get_entry_by_id(self, file_id: str) -> Optional[dict]:
        query = "SELECT * FROM history WHERE file_id = ?"
        rows = await db.execute(query, (file_id,))
        return rows[0] if rows else None
        
    async def delete_entry(self, file_id: str) -> bool:
        query = "DELETE FROM history WHERE file_id = ?"
        await db.execute(query, (file_id,))
        return True

    async def update_entry_status(self, file_id: str, status: str):
        query = "UPDATE history SET status = ? WHERE file_id = ?"
        await db.execute(query, (status, file_id))

history_repo = HistoryRepository()
