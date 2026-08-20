from backend.database.sqlite import db
from backend.models.settings import SettingsModel

class SettingsRepository:
    async def get_settings(self) -> SettingsModel:
        query = "SELECT * FROM settings LIMIT 1"
        rows = await db.execute(query)
        if not rows:
            # Fallback if somehow not initialized
            return SettingsModel()
        row = rows[0]
        return SettingsModel(
            worker_count=row["worker_count"],
            retry_count=row["retry_count"],
            search_delay=row["search_delay"],
            scroll_delay=row["scroll_delay"],
            website_timeout=row["website_timeout"],
            google_timeout=row["google_timeout"],
            enable_scraping=bool(row["enable_scraping"]),
            enable_translation=bool(row["enable_translation"]),
            enable_ai=bool(row["enable_ai"]),
            enable_cache=bool(row["enable_cache"]),
            output_directory=row["output_directory"],
            checkpoint_interval=row["checkpoint_interval"]
        )
        
    async def save_settings(self, settings: SettingsModel) -> bool:
        query = """
        UPDATE settings SET
            worker_count = ?,
            retry_count = ?,
            search_delay = ?,
            scroll_delay = ?,
            website_timeout = ?,
            google_timeout = ?,
            enable_scraping = ?,
            enable_translation = ?,
            enable_ai = ?,
            enable_cache = ?,
            output_directory = ?,
            checkpoint_interval = ?
        WHERE id = 1
        """
        params = (
            settings.worker_count,
            settings.retry_count,
            settings.search_delay,
            settings.scroll_delay,
            settings.website_timeout,
            settings.google_timeout,
            1 if settings.enable_scraping else 0,
            1 if settings.enable_translation else 0,
            1 if settings.enable_ai else 0,
            1 if settings.enable_cache else 0,
            settings.output_directory,
            settings.checkpoint_interval
        )
        await db.execute(query, params)
        return True

settings_repo = SettingsRepository()
