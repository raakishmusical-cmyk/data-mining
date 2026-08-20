import json
from datetime import datetime
from backend.database.sqlite import db
from backend.utils.logger import logger

class CheckpointManager:
    async def create_checkpoint(self, job_id: str, district: str, keyword: str, business_index: int, statistics: dict, queue_state: dict):
        """Saves current mining queue and progress state into checkpoints database."""
        try:
            timestamp = datetime.now().isoformat()
            stats_json = json.dumps(statistics)
            queue_json = json.dumps(queue_state)
            
            query = """
            INSERT OR REPLACE INTO checkpoints (job_id, district, keyword, business_index, statistics, queue_state, timestamp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """
            await db.execute(query, (job_id, district, keyword, business_index, stats_json, queue_json, timestamp))
            logger.debug(f"Checkpoint saved for job {job_id}: Dist={district}, KW={keyword}, Idx={business_index}")
        except Exception as e:
            logger.error(f"Failed to create checkpoint: {e}", exc_info=True)

    async def get_checkpoint(self, job_id: str) -> dict:
        """Retrieves a checkpoint by job_id."""
        query = "SELECT * FROM checkpoints WHERE job_id = ?"
        rows = await db.execute(query, (job_id,))
        if not rows:
            return {}
        row = rows[0]
        return {
            "job_id": row["job_id"],
            "district": row["district"],
            "keyword": row["keyword"],
            "business_index": row["business_index"],
            "statistics": json.loads(row["statistics"]),
            "queue_state": json.loads(row["queue_state"]),
            "timestamp": row["timestamp"]
        }

    async def delete_checkpoint(self, job_id: str):
        """Removes a checkpoint after a job finishes or is fully stopped."""
        query = "DELETE FROM checkpoints WHERE job_id = ?"
        await db.execute(query, (job_id,))
        logger.info(f"Checkpoint deleted for job {job_id}.")

checkpoint_manager = CheckpointManager()
