import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH
from data.schema import SCHEMA_QUERIES

class Repository:
    def __init__(self):
        # One connection to rule them all (prevents nesting deadlocks)
        self.conn = sqlite3.connect(DB_PATH, timeout=20, check_same_thread=False)
        # Enable WAL mode for better concurrency (The Master Architect way)
        self.conn.execute("PRAGMA journal_mode=WAL")
        self.conn.execute("PRAGMA synchronous=NORMAL")
        self._init_db()

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        cursor = self.conn.cursor()
        for query in SCHEMA_QUERIES:
            cursor.execute(query)
        
        # Migration: Add state_context to existing user_state table (Rule 5: Idempotency)
        try:
            cursor.execute("ALTER TABLE user_state ADD COLUMN state_context TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists

        # Migration: Add photo_paths to existing activities table
        try:
            cursor.execute("ALTER TABLE activities ADD COLUMN photo_paths TEXT")
        except sqlite3.OperationalError:
            pass # Column already exists
            
        self.conn.commit()

    # --- Activity Methods ---
    def start_activity(self, user_id, name):
        cursor = self.conn.cursor()
        start_time = datetime.now()
        cursor.execute(
            "INSERT INTO activities (user_id, name, start_time) VALUES (?, ?, ?)",
            (user_id, name, start_time)
        )
        activity_id = cursor.lastrowid
        self.conn.commit()
        self.update_user_state(user_id, current_activity_id=activity_id, last_activity_name=name)
        return activity_id

    def stop_activity(self, activity_id):
        cursor = self.conn.cursor()
        end_time = datetime.now()
        
        cursor.execute("SELECT start_time FROM activities WHERE id = ?", (activity_id,))
        row = cursor.fetchone()
        if not row: return 0
        
        start_time_str = row[0]
        start_time = datetime.fromisoformat(start_time_str)
        
        duration = int((end_time - start_time).total_seconds())
        cursor.execute(
            "UPDATE activities SET end_time = ?, duration = ? WHERE id = ?",
            (end_time, duration, activity_id)
        )
        self.conn.commit()
        return duration

    def get_active_activity(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT current_activity_id FROM user_state WHERE user_id = ?",
            (user_id,)
        )
        row = cursor.fetchone()
        if row and row[0]:
            return row[0]
        return None

    # --- State Management ---
    def update_user_state(self, user_id, **kwargs):
        cursor = self.conn.cursor()
        
        # Check if user exists
        cursor.execute("SELECT user_id FROM user_state WHERE user_id = ?", (user_id,))
        if not cursor.fetchone():
            cursor.execute("INSERT INTO user_state (user_id) VALUES (?)", (user_id,))
        
        for key, value in kwargs.items():
            cursor.execute(f"UPDATE user_state SET {key} = ? WHERE user_id = ?", (value, user_id))
        self.conn.commit()

    def get_user_state(self, user_id):
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM user_state WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return dict(row) if row else {}

    # --- Spending Methods ---
    def log_spending(self, user_id, amount, category, date=None, payment_method="PalmPay"):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO spending (user_id, amount, category, date, payment_method) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, payment_method)
        )
        self.conn.commit()
        return cursor.lastrowid

    # --- Reminder Methods ---
    def set_reminder(self, user_id, text, reminder_date, recurring=False):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, text, reminder_date, recurring) VALUES (?, ?, ? , ?)",
            (user_id, text, reminder_date, recurring)
        )
        self.conn.commit()
        return cursor.lastrowid

    def add_person(self, user_id, name, relationship):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO people (user_id, name, relationship) VALUES (?, ?, ?)",
            (user_id, name, relationship)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_activity_name(self, activity_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM activities WHERE id = ?", (activity_id,))
        row = cursor.fetchone()
        return row[0] if row else "Unknown"

    # --- Phase 2: Media Management ---
    def add_pending_media(self, user_id, file_path):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO pending_media (user_id, file_path) VALUES (?, ?)",
            (user_id, file_path)
        )
        self.conn.commit()

    def get_pending_media(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_path FROM pending_media WHERE user_id = ?", (user_id,))
        rows = cursor.fetchall()
        return [row[0] for row in rows]

    def clear_pending_media(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM pending_media WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def complete_activity_with_media(self, user_id, name):
        """Fetches pending photos, saves activity, and clears pending queue."""
        photo_paths = self.get_pending_media(user_id)
        cursor = self.conn.cursor()
        start_time = datetime.now()
        paths_json = json.dumps(photo_paths)
        
        cursor.execute(
            "INSERT INTO activities (user_id, name, start_time, photo_paths) VALUES (?, ?, ?, ?)",
            (user_id, name, start_time, paths_json)
        )
        activity_id = cursor.lastrowid
        self.conn.commit()
        
        # Cleanup (Rule 14: Data Minimization)
        self.clear_pending_media(user_id)
        self.update_user_state(user_id, current_activity_id=activity_id, last_activity_name=name, state_context=None)
        return activity_id

    def check_path_exists(self, relative_path):
        """Checks if a file path is mentioned in activities or pending_media."""
        cursor = self.conn.cursor()
        # Check pending_media
        cursor.execute("SELECT id FROM pending_media WHERE file_path = ?", (relative_path,))
        if cursor.fetchone(): return True
        
        # Check activities (using LIKE because it's in a JSON array string)
        # Rule: SQLite JSON extracts are better but LIKE works for simple relative paths
        cursor.execute("SELECT id FROM activities WHERE photo_paths LIKE ?", (f'%{relative_path}%',))
        if cursor.fetchone(): return True
        
        return False
