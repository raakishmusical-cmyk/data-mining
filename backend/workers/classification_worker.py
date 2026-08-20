import json
from datetime import datetime
from backend.utils.logger import logger
from backend.utils.industry import determine_industry
from backend.utils.tags import determine_tag
from backend.database.sqlite import db

class ClassificationWorker:
    async def classify(self, category: str, name: str, search_keyword: str, enable_ai: bool = False) -> tuple[str, str]:
        """
        Determines the Industry and Tag.
        Always returns (search_keyword, "Sports Lead") per requirements.
        """
        return search_keyword, "Sports Lead"

classification_worker = ClassificationWorker()
