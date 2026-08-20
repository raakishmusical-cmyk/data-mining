import sqlite3
import os
import asyncio
from pathlib import Path
from backend.database.schema import CREATE_TABLES_SQL, DEFAULT_SETTINGS_SQL
from backend.utils.logger import logger

DB_PATH = "Output/Database/harvester.db"

class DatabaseManager:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path
        self._lock = asyncio.Lock()
        
    def initialize_db(self):
        """Initializes tables and directory structure. Done synchronously on startup."""
        try:
            db_dir = Path(self.db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)
            
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Execute schemas
            for sql in CREATE_TABLES_SQL:
                cursor.execute(sql)
            
            # Insert default configurations
            cursor.execute(DEFAULT_SETTINGS_SQL)
            
            # Seed default keywords
            default_kws = [
                "Sports Shop", "Sports Store", "Sporting Goods Store", "Gym", "Fitness Center",
                "Yoga Studio", "School", "College", "University", "Sports Academy", "Sports Club",
                "Stadium", "Playground", "Indoor Sports Complex", "Hotel", "Resort", "Hospital",
                "Rehabilitation Center", "Physiotherapy Clinic", "Rehabilitation Clinic",
                "Bowling Alley", "Golf Club", "Sports Franchise", "Country Club", "Social Club",
                "Cruise Line", "Holiday Park",
               
            ]
            for kw in default_kws:
                cursor.execute("INSERT OR IGNORE INTO keywords (keyword, is_default) VALUES (?, 1)", (kw,))
            
            conn.commit()
            conn.close()
            logger.info("SQLite Database initialized and seeded successfully.")
        except Exception as e:
            logger.error(f"Database initialization failed: {e}", exc_info=True)
            raise e

    def _execute(self, query: str, params: tuple = ()):
        """Internal synchronous execution function."""
        conn = sqlite3.connect(self.db_path)
        # Enable Dict-like row return formatting
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        try:
            cursor.execute(query, params)
            if query.strip().upper().startswith(("INSERT", "UPDATE", "DELETE", "REPLACE")):
                conn.commit()
                lastrowid = cursor.lastrowid
                conn.close()
                return lastrowid
            else:
                rows = [dict(row) for row in cursor.fetchall()]
                conn.close()
                return rows
        except Exception as e:
            conn.rollback()
            conn.close()
            logger.error(f"SQL execution error on query '{query}': {e}")
            raise e

    async def execute(self, query: str, params: tuple = ()):
        """Asynchronously executes a query in the thread pool, thread-safe."""
        async with self._lock:
            return await asyncio.to_thread(self._execute, query, params)

db = DatabaseManager()
