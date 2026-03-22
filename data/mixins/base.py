import json
import sqlite3
from datetime import datetime

class BaseMixin:
    """Base class to provide sqlite connection access to mixins."""
    conn: sqlite3.Connection

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
