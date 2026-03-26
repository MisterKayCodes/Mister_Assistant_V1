import json
import sqlite3
from datetime import datetime, timedelta
from data.mixins.base import BaseMixin

class TaskMixin(BaseMixin):
    def add_task_group(self, user_id, task_list, duration_minutes):
        """Adds a new task group and returns its ID."""
        cursor = self.conn.cursor()
        start_time = datetime.now()
        end_time = start_time + timedelta(minutes=duration_minutes)
        
        cursor.execute(
            """
            INSERT INTO tasks (user_id, task_list, duration_minutes, start_time, end_time, status)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (user_id, json.dumps(task_list), duration_minutes, start_time, end_time, 'pending')
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_task_by_id(self, task_id):
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        return dict(row) if row else None

    def get_active_task_group(self, user_id):
        """Returns the most recent pending task group for a user."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM tasks WHERE user_id = ? AND status = 'pending' ORDER BY start_time DESC LIMIT 1",
            (user_id,)
        )
        row = cursor.fetchone()
        return dict(row) if row else None

    def update_task_status(self, task_id, status, completed_indices=None, end_time=None):
        """Updates task status, completed indices, or end_time (for snooze)."""
        cursor = self.conn.cursor()
        updates = []
        params = []
        
        if status:
            updates.append("status = ?")
            params.append(status)
        if completed_indices is not None:
            updates.append("completed_indices = ?")
            params.append(json.dumps(completed_indices))
        if end_time:
            updates.append("end_time = ?")
            params.append(end_time)
            
        if not updates:
            return
            
        sql = f"UPDATE tasks SET {', '.join(updates)} WHERE id = ?"
        params.append(task_id)
        cursor.execute(sql, tuple(params))
        self.conn.commit()

    def log_task_completion(self, task_id, user_id, completed_items, original_task_list, notes):
        """Logs the final results of a task session."""
        cursor = self.conn.cursor()
        cursor.execute(
            """
            INSERT INTO task_logs (task_id, user_id, completed_items, original_task_list, notes)
            VALUES (?, ?, ?, ?, ?)
            """,
            (task_id, user_id, json.dumps(completed_items), json.dumps(original_task_list), notes)
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_task_history(self, user_id, limit=10):
        """Retrieves past task logs for a user."""
        self.conn.row_factory = sqlite3.Row
        cursor = self.conn.cursor()
        cursor.execute(
            "SELECT * FROM task_logs WHERE user_id = ? ORDER BY created_at DESC LIMIT ?",
            (user_id, limit)
        )
        return [dict(row) for row in cursor.fetchall()]
