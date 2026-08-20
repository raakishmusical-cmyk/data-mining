from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any

class MiningJobModel(BaseModel):
    job_id: str
    status: str # 'Idle', 'Starting', 'Running', 'Paused', 'Stopping', 'Stopped', 'Completed', 'Failed'
    current_state: Optional[str] = None
    current_district: Optional[str] = None
    current_keyword: Optional[str] = None
    processed_businesses: int = 0
    failed_businesses: int = 0
    started_at: str
    finished_at: Optional[str] = None

class JobCheckpointModel(BaseModel):
    job_id: str
    district: str
    keyword: str
    business_index: int
    statistics: Dict[str, Any]
    queue_state: Dict[str, Any]
    timestamp: str

class StatisticsModel(BaseModel):
    businesses_found: int = 0
    businesses_saved: int = 0
    duplicates_skipped: int = 0
    phone_count: int = 0
    mobile_count: int = 0
    email_count: int = 0
    website_count: int = 0
    instagram_count: int = 0
    facebook_count: int = 0
    linkedin_count: int = 0
    twitter_count: int = 0
    youtube_count: int = 0
    error_count: int = 0
    retry_count: int = 0
    elapsed_time: int = 0
