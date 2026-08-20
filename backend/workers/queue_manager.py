import asyncio
from backend.utils.logger import logger

class QueueManager:
    def __init__(self):
        self.is_paused = False
        self.is_stopped = False
        self.current_job_id = None
        
        # Async queues
        self.district_queue = asyncio.Queue()
        self.keyword_queue = asyncio.Queue()
        self.website_queue = asyncio.Queue()
        self.classification_queue = asyncio.Queue()
        self.save_queue = asyncio.Queue()
        
    def reset(self):
        self.is_paused = False
        self.is_stopped = False
        self.current_job_id = None
        
        # Empty queues by recreating them
        self.district_queue = asyncio.Queue()
        self.keyword_queue = asyncio.Queue()
        self.website_queue = asyncio.Queue()
        self.classification_queue = asyncio.Queue()
        self.save_queue = asyncio.Queue()
        logger.info("Queue manager states and queues reset successfully.")

    async def wait_if_paused(self):
        """Yield control and sleep while the pause state is active."""
        while self.is_paused and not self.is_stopped:
            await asyncio.sleep(0.5)

    def pause(self):
        self.is_paused = True
        logger.info("Queue Manager paused processing.")

    def resume(self):
        self.is_paused = False
        logger.info("Queue Manager resumed processing.")

    def stop(self):
        self.is_stopped = True
        self.is_paused = False
        logger.info("Queue Manager stopped processing.")

queue_manager = QueueManager()
