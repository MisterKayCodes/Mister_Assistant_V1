import sqlite3
import json
import os
from datetime import datetime
from config import DB_PATH

class Repository:
    def __init__(self):
        self._init_db()

    def _get_connection(self):
        return sqlite3.connect(DB_PATH)

    def _init_db(self):
        os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Activities table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS activities (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    name TEXT,
                    start_time TIMESTAMP,
                    end_time TIMESTAMP,
                    duration INTEGER
                )
            """)
            
            # People table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS people (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    name TEXT,
                    relationship TEXT,
                    birthday TEXT,
                    facts TEXT -- JSON string
                )
            """)
            
            # Spending table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS spending (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    amount REAL,
                    category TEXT,
                    date TEXT,
                    payment_method TEXT
                )
            """)
            
            # Reminders table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS reminders (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    text TEXT,
                    reminder_date TIMESTAMP,
                    recurring BOOLEAN,
                    is_sent BOOLEAN DEFAULT 0
                )
            """)
            
            # User state for Soft Context Memory
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS user_state (
                    user_id TEXT PRIMARY KEY,
                    current_activity_id INTEGER,
                    last_person_id INTEGER,
                    last_intent TEXT,
                    last_activity_name TEXT
                )
            """)
            conn.commit()

    # --- Activity Methods ---
    def start_activity(self, user_id, name):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            start_time = datetime.now()
            cursor.execute(
                "INSERT INTO activities (user_id, name, start_time) VALUES (?, ?, ?)",
                (user_id, name, start_time)
            )
            activity_id = cursor.lastrowid
            self.update_user_state(user_id, current_activity_id=activity_id, last_activity_name=name)
            return activity_id

    def stop_activity(self, activity_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            end_time = datetime.now()
            
            cursor.execute("SELECT start_time FROM activities WHERE id = ?", (activity_id,))
            start_time_str = cursor.fetchone()[0]
            start_time = datetime.fromisoformat(start_time_str)
            
            duration = int((end_time - start_time).total_seconds())
            cursor.execute(
                "UPDATE activities SET end_time = ?, duration = ? WHERE id = ?",
                (end_time, duration, activity_id)
            )
            return duration

    def get_active_activity(self, user_id):
        with self._get_connection() as conn:
            cursor = conn.cursor()
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
        with self._get_connection() as conn:
            cursor = conn.cursor()
            
            # Check if user exists
            cursor.execute("SELECT user_id FROM user_state WHERE user_id = ?", (user_id,))
            if not cursor.fetchone():
                cursor.execute("INSERT INTO user_state (user_id) VALUES (?)", (user_id,))
            
            for key, value in kwargs.items():
                cursor.execute(f"UPDATE user_state SET {key} = ? WHERE user_id = ?", (value, user_id))
            conn.commit()

    def get_user_state(self, user_id):
        with self._get_connection() as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM user_state WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            return dict(row) if row else {}

    # --- Spending Methods ---
    def log_spending(self, user_id, amount, category, date=None, payment_method="PalmPay"):
        if not date:
            date = datetime.now().strftime("%Y-%m-%d")
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO spending (user_id, amount, category, date, payment_method) VALUES (?, ?, ?, ?, ?)",
                (user_id, amount, category, date, payment_method)
            )
            return cursor.lastrowid

    # --- Reminder Methods ---
    def set_reminder(self, user_id, text, reminder_date, recurring=False):
        with self._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO reminders (user_id, text, reminder_date, recurring) VALUES (?, ?, ?, ?)",
                (user_id, text, reminder_date, recurring)
            )
            return cursor.lastrowid
