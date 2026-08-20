from pydantic import BaseModel, Field

class SettingsModel(BaseModel):
    worker_count: int = Field(30, ge=1, le=100)
    retry_count: int = Field(3, ge=0, le=10)
    search_delay: int = Field(1500, ge=0, le=10000)
    scroll_delay: int = Field(1500, ge=0, le=10000)
    website_timeout: int = Field(10000, ge=1000, le=60000)
    google_timeout: int = Field(20000, ge=5000, le=120000)
    enable_scraping: bool = True
    enable_translation: bool = True
    enable_ai: bool = False
    enable_cache: bool = True
    output_directory: str = "Output"
    checkpoint_interval: int = Field(60, ge=10, le=600)
