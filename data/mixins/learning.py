import sqlite3

class LearningMixin:
    def _init_learning(self):
        cursor = self.conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS custom_patterns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                phrase TEXT,
                target_intent TEXT,
                is_template BOOLEAN DEFAULT 0,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.conn.commit()

    def add_custom_pattern(self, user_id, phrase, intent, is_template=False):
        cursor = self.conn.cursor()
        # Clean phrases for lookup
        phrase = phrase.lower().strip()
        cursor.execute("""
            INSERT INTO custom_patterns (user_id, phrase, target_intent, is_template)
            VALUES (?, ?, ?, ?)
        """, (user_id, phrase, intent, 1 if is_template else 0))
        self.conn.commit()

    def get_user_patterns(self, user_id):
        cursor = self.conn.cursor()
        cursor.execute("SELECT phrase, target_intent, is_template FROM custom_patterns WHERE user_id = ?", (user_id,))
        return [{"phrase": r[0], "intent": r[1], "is_template": bool(r[2])} for r in cursor.fetchall()]

    def delete_custom_pattern(self, user_id, phrase):
        cursor = self.conn.cursor()
        cursor.execute("DELETE FROM custom_patterns WHERE user_id = ? AND phrase = ?", (user_id, phrase.lower()))
        self.conn.commit()
