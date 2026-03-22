import sqlite3
import os
from config import DB_PATH
from data.schema import SCHEMA_QUERIES
from data.mixins import (
    ActivityMixin, StateMixin, SpendingMixin, 
    PeopleMixin, ReminderMixin, MediaMixin
)

class Repository(
    ActivityMixin, StateMixin, SpendingMixin, 
    PeopleMixin, ReminderMixin, MediaMixin
):
    def __init__(self):
        # One connection to rule them all (prevents nesting deadlocks)
        self.conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
        # Enable WAL mode for better concurrency (The Master Architect way)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

    def _init_db(self):
        """Initializes tables and performs migrations."""
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        cursor = self.conn.cursor()
        for query in SCHEMA_QUERIES:
            cursor.execute(query)
            
        # Migrations (Rule 5: Idempotency)
        try:
            cursor.execute("ALTER TABLE user_state ADD COLUMN state_context TEXT")
        except sqlite3.OperationalError: pass

        try:
            # For 2-Step Reset Safety (Phase 4)
            cursor.execute("ALTER TABLE user_state ADD COLUMN reset_code INTEGER")
        except sqlite3.OperationalError: pass

        try:
            # For Surgical Correction (Phase 5)
            cursor.execute("ALTER TABLE user_state ADD COLUMN correction_options TEXT")
            cursor.execute("ALTER TABLE user_state ADD COLUMN correction_new_info TEXT")
        except sqlite3.OperationalError: pass
        
        try:
            cursor.execute("ALTER TABLE activities ADD COLUMN photo_paths TEXT")
        except sqlite3.OperationalError: pass
            
        self.conn.commit()

    def clear_all_user_data(self, user_id):
        """ मास्टर आर्किटेक्ट (Master Architect) Rule 9: The Nuclear Reset. """
        cursor = self.conn.cursor()
        tables = ["activities", "spending", "people", "reminders", "user_state"]
        for table in tables:
            cursor.execute(f"DELETE FROM {table} WHERE user_id = ?", (user_id,))
        self.conn.commit()
