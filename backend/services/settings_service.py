from backend.repositories.settings_repository import settings_repo
from backend.models.settings import SettingsModel

class SettingsService:
    async def get_settings(self) -> SettingsModel:
        return await settings_repo.get_settings()
        
    async def save_settings(self, settings: SettingsModel) -> bool:
        return await settings_repo.save_settings(settings)

settings_service = SettingsService()
