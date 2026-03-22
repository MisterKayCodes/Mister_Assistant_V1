import json
from datetime import datetime
from data.mixins.base import BaseMixin

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
        """Atomic Update with Rollback."""
        cursor = self.conn.cursor()
        cursor.execute("SELECT user_id, name, start_time, end_time FROM activities WHERE id = ?", (activity_id,))
        old = cursor.fetchone()
        if not old: return None
        
        uid, old_name, old_start, old_end = old
        new_name = name if name else old_name
        new_start = start if start else old_start
        new_end = end if end else old_end
        
        conflicts = self.check_for_conflicts(uid, new_start, new_end, exclude_id=activity_id)
        if conflicts:
            return {"status": "conflict", "conflicts": conflicts}
            
        cursor.execute(
            "UPDATE activities SET name = ?, start_time = ?, end_time = ? WHERE id = ?",
            (new_name, new_start, new_end, activity_id)
        )
        self.conn.commit()
        return {"status": "success", "old": old, "new": (uid, new_name, new_start, new_end)}
