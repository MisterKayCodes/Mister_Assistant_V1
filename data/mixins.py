import json
import sqlite3
from datetime import datetime
from data.schema import SCHEMA_QUERIES

class BaseMixin:
    """Base class to provide sqlite connection access to mixins."""
    conn: sqlite3.Connection

class ActivityMixin(BaseMixin):
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
        start_time = datetime.fromisoformat(row[0])
        duration = int((end_time - start_time).total_seconds())
        cursor.execute(
            "UPDATE activities SET end_time = ?, duration = ? WHERE id = ?",
            (end_time, duration, activity_id)
        )
        self.conn.commit()
        return duration

    def get_active_activity(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT current_activity_id FROM user_state WHERE user_id = ?", (user_id,))
        row = cursor.fetchone()
        return row[0] if row else None

    def get_activity_name(self, activity_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM activities WHERE id = ?", (activity_id,))
        row = cursor.fetchone()
        return row[0] if row else "Unknown"

class StateMixin(BaseMixin):
    def update_user_state(self, user_id, **kwargs):
        cursor = self.conn.cursor()
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

class SpendingMixin(BaseMixin):
    def log_spending(self, user_id, amount, category, date=None, payment_method="PalmPay"):
        if not date: date = datetime.now().strftime("%Y-%m-%d")
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO spending (user_id, amount, category, date, payment_method) VALUES (?, ?, ?, ?, ?)",
            (user_id, amount, category, date, payment_method)
        )
        self.conn.commit()
        return cursor.lastrowid

class PeopleMixin(BaseMixin):
    def add_person(self, user_id, name, relationship):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO people (user_id, name, relationship) VALUES (?, ?, ?)",
            (user_id, name, relationship)
        )
        self.conn.commit()
        return cursor.lastrowid

class ReminderMixin(BaseMixin):
    def set_reminder(self, user_id, text, reminder_date, recurring=False):
        cursor = self.conn.cursor()
        cursor.execute(
            "INSERT INTO reminders (user_id, text, reminder_date, recurring) VALUES (?, ?, ? , ?)",
            (user_id, text, reminder_date, recurring)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_due_reminders(self):
        cursor = self.conn.cursor()
        now = datetime.now()
        cursor.execute(
            "SELECT id, user_id, text FROM reminders WHERE is_sent = 0 AND datetime(reminder_date) <= datetime(?)",
            (now,)
        )
        return cursor.fetchall()

    def mark_reminder_sent(self, reminder_id):
        cursor = self.conn.cursor()
        cursor.execute("UPDATE reminders SET is_sent = 1 WHERE id = ?", (reminder_id,))
        self.conn.commit()

class MediaMixin(BaseMixin):
    def add_pending_media(self, user_id, file_path):
        cursor = self.conn.cursor()
        cursor.execute("INSERT INTO pending_media (user_id, file_path) VALUES (?, ?)", (user_id, file_path))
        self.conn.commit()

    def get_pending_media(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT file_path FROM pending_media WHERE user_id = ?", (user_id,))
        return [row[0] for row in cursor.fetchall()]

    def clear_pending_media(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM pending_media WHERE user_id = ?", (user_id,))
        self.conn.commit()

    def complete_activity_with_media(self, user_id, name):
        photo_paths = self.get_pending_media(user_id)
        cursor = self.conn.cursor()
        paths_json = json.dumps(photo_paths)
        cursor.execute(
            "INSERT INTO activities (user_id, name, start_time, photo_paths) VALUES (?, ?, ?, ?)",
            (user_id, name, datetime.now(), paths_json)
        )
        act_id = cursor.lastrowid
        self.conn.commit()
        self.clear_pending_media(user_id)
        self.update_user_state(user_id, current_activity_id=act_id, last_activity_name=name, state_context=None)
        return act_id

    def log_retro_activity(self, user_id, name, start_time, end_time, photo_paths=None):
        """Inserts a past activity directly into the history."""
        cursor = self.conn.cursor()
        paths_json = json.dumps(photo_paths or [])
        duration = int((end_time - start_time).total_seconds())
        cursor.execute(
            "INSERT INTO activities (user_id, name, start_time, end_time, duration, photo_paths) VALUES (?, ?, ?, ?, ?, ?)",
            (user_id, name, start_time, end_time, duration, paths_json)
        )
        self.conn.commit()
        return cursor.lastrowid

    def check_for_conflicts(self, user_id, start_time, end_time, exclude_id=None):
        """Checks for overlaps. Rule 9: Can exclude an ID (Surgical Update)."""
        cursor = self.conn.cursor()
        now = datetime.now()
        query = """SELECT id, name FROM activities 
                   WHERE user_id = ? 
                   AND datetime(start_time) < datetime(?) 
                   AND datetime(COALESCE(end_time, ?)) > datetime(?)"""
        params = [user_id, end_time, now, start_time]
        
        if exclude_id:
            query += " AND id != ?"
            params.append(exclude_id)
            
        cursor.execute(query, tuple(params))
        return [{"id": row[0], "name": row[1]} for row in cursor.fetchall()]

    def find_activities_at_time(self, user_id, timestamp):
        """Surgical Search Rule 10: Find what was happening at a specific time."""
        cursor = self.conn.cursor()
        # Find any activity where (start <= timestamp < end)
        # For ongoing, end matches 'now'
        now = datetime.now()
        cursor.execute(
            """SELECT id, name, start_time, end_time FROM activities 
               WHERE user_id = ? 
               AND datetime(start_time) <= datetime(?) 
               AND datetime(COALESCE(end_time, ?)) >= datetime(?)""",
            (user_id, timestamp, now, timestamp)
        )
        return [{"id": row[0], "name": row[1], "start": row[2], "end": row[3]} for row in cursor.fetchall()]

    def update_activity(self, activity_id, name=None, start=None, end=None):
        """मास्टर आर्किटेक्ट (Master Architect) Rule 12: Atomic Update with Rollback."""
        cursor = self.conn.cursor()
        # 1. Get current state for rollback/diff
        cursor.execute("SELECT user_id, name, start_time, end_time FROM activities WHERE id = ?", (activity_id,))
        old = cursor.fetchone()
        if not old: return None
        
        uid, old_name, old_start, old_end = old
        new_name = name if name else old_name
        new_start = start if start else old_start
        new_end = end if end else old_end
        
        # 2. Re-trigger Conflict Engine (Rule 1)
        conflicts = self.check_for_conflicts(uid, new_start, new_end, exclude_id=activity_id)
        if conflicts:
            return {"status": "conflict", "conflicts": conflicts}
            
        # 3. Update
        cursor.execute(
            "UPDATE activities SET name = ?, start_time = ?, end_time = ? WHERE id = ?",
            (new_name, new_start, new_end, activity_id)
        )
        self.conn.commit()
        return {"status": "success", "old": old, "new": (uid, new_name, new_start, new_end)}

    def check_path_exists(self, relative_path):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM pending_media WHERE file_path = ?", (relative_path,))
        if cursor.fetchone(): return True
        cursor.execute("SELECT id FROM activities WHERE photo_paths LIKE ?", (f'%{relative_path}%',))
        return cursor.fetchone() is not None
