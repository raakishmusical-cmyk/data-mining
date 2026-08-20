CREATE_TABLES_SQL = [
    """
    CREATE TABLE IF NOT EXISTS settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        worker_count INTEGER DEFAULT 30,
        retry_count INTEGER DEFAULT 3,
        search_delay INTEGER DEFAULT 1500,
        scroll_delay INTEGER DEFAULT 1500,
        website_timeout INTEGER DEFAULT 10000,
        google_timeout INTEGER DEFAULT 20000,
        enable_scraping INTEGER DEFAULT 1,
        enable_translation INTEGER DEFAULT 1,
        enable_ai INTEGER DEFAULT 0,
        enable_cache INTEGER DEFAULT 1,
        output_directory TEXT DEFAULT 'Output',
        checkpoint_interval INTEGER DEFAULT 60
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS history (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        file_id TEXT UNIQUE NOT NULL,
        file_name TEXT NOT NULL,
        category TEXT NOT NULL, -- 'Mining Files', 'Marked Files', 'Cleaned Files', 'Processed Files'
        district TEXT NOT NULL,
        keyword_count INTEGER DEFAULT 0,
        row_count INTEGER DEFAULT 0,
        file_size TEXT NOT NULL,
        created_at TEXT NOT NULL,
        status TEXT DEFAULT 'ready'
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS jobs (
        job_id TEXT PRIMARY KEY,
        status TEXT NOT NULL, -- 'Running', 'Paused', 'Stopped', 'Completed', 'Failed'
        current_state TEXT,
        current_district TEXT,
        current_keyword TEXT,
        processed_businesses INTEGER DEFAULT 0,
        failed_businesses INTEGER DEFAULT 0,
        started_at TEXT NOT NULL,
        finished_at TEXT
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS checkpoints (
        job_id TEXT PRIMARY KEY,
        district TEXT NOT NULL,
        keyword TEXT NOT NULL,
        business_index INTEGER DEFAULT 0,
        statistics TEXT NOT NULL, -- JSON string
        queue_state TEXT NOT NULL,  -- JSON string
        timestamp TEXT NOT NULL,
        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        timestamp TEXT NOT NULL,
        level TEXT NOT NULL,
        message TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS statistics (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id TEXT NOT NULL,
        businesses_found INTEGER DEFAULT 0,
        businesses_saved INTEGER DEFAULT 0,
        duplicates_skipped INTEGER DEFAULT 0,
        phone_count INTEGER DEFAULT 0,
        mobile_count INTEGER DEFAULT 0,
        email_count INTEGER DEFAULT 0,
        website_count INTEGER DEFAULT 0,
        instagram_count INTEGER DEFAULT 0,
        facebook_count INTEGER DEFAULT 0,
        linkedin_count INTEGER DEFAULT 0,
        twitter_count INTEGER DEFAULT 0,
        youtube_count INTEGER DEFAULT 0,
        error_count INTEGER DEFAULT 0,
        retry_count INTEGER DEFAULT 0,
        elapsed_time INTEGER DEFAULT 0,
        FOREIGN KEY (job_id) REFERENCES jobs(job_id) ON DELETE CASCADE
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS cache (
        key TEXT PRIMARY KEY,
        value TEXT NOT NULL, -- JSON string
        created_at TEXT NOT NULL
    );
    """,
    """
    CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        keyword TEXT UNIQUE NOT NULL,
        is_default INTEGER DEFAULT 0
    );
    """
]

# Insert default settings if not exists
DEFAULT_SETTINGS_SQL = """
INSERT INTO settings (
    worker_count, retry_count, search_delay, scroll_delay, website_timeout, 
    google_timeout, enable_scraping, enable_translation, enable_ai, enable_cache, 
    output_directory, checkpoint_interval
) SELECT 30, 3, 1500, 1500, 10000, 20000, 1, 1, 0, 1, 'Output', 60
WHERE NOT EXISTS (SELECT 1 FROM settings);
"""
