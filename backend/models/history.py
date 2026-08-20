from pydantic import BaseModel
from typing import Optional

class HistoryItemModel(BaseModel):
    id: Optional[int] = None
    file_id: str
    file_name: str
    category: str
    district: str
    keyword_count: int
    row_count: int
    file_size: str
    created_at: str
    status: str = "ready"
