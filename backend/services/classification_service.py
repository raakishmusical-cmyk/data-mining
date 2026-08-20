from backend.workers.classification_worker import classification_worker

class ClassificationService:
    async def classify_business(self, category: str, name: str, search_keyword: str, enable_ai: bool = False) -> tuple[str, str]:
        return await classification_worker.classify(category, name, search_keyword, enable_ai)

classification_service = ClassificationService()
