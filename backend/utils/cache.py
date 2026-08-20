import json
from datetime import datetime
from backend.database.sqlite import db

class SQLiteCache:
    async def get(self, key: str):
        query = "SELECT value FROM cache WHERE key = ?"
        rows = await db.execute(query, (key,))
        if rows:
            return json.loads(rows[0]["value"])
        return None

    async def set(self, key: str, value: any):
        val_str = json.dumps(value)
        now = datetime.now().isoformat()
        query = "INSERT OR REPLACE INTO cache (key, value, created_at) VALUES (?, ?, ?)"
        await db.execute(query, (key, val_str, now))

    async def clear(self):
        await db.execute("DELETE FROM cache")

cache = SQLiteCache()
