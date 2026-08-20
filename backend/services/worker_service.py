from backend.workers.queue_manager import queue_manager

class WorkerService:
    async def get_worker_status(self) -> dict:
        return {
            "is_paused": queue_manager.is_paused,
            "is_stopped": queue_manager.is_stopped,
            "current_job_id": queue_manager.current_job_id
        }

worker_service = WorkerService()
