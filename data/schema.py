SCHEMA_QUERIES = [
    """
    CREATE TABLE IF NOT EXISTS activities (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        name TEXT,
        start_time TIMESTAMP,
        end_time TIMESTAMP,
        duration INTEGER,
        photo_paths TEXT -- JSON array of relative paths
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS people (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        name TEXT,
        relationship TEXT,
        birthday TEXT,
        facts TEXT -- JSON string
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS spending (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        amount REAL,
        category TEXT,
        date TEXT,
        payment_method TEXT
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS reminders (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        text TEXT,
        reminder_date TIMESTAMP,
        recurring BOOLEAN,
        is_sent BOOLEAN DEFAULT 0
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS user_state (
        user_id TEXT PRIMARY KEY,
        current_activity_id INTEGER,
        last_person_id INTEGER,
        last_intent TEXT,
        last_activity_name TEXT,
        state_context TEXT -- e.g. 'WAITING_FOR_CAPTION'
    )
    """,
    """
    CREATE TABLE IF NOT EXISTS pending_media (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT,
        file_path TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """
]
