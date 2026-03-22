import json
from datetime import datetime
from data.mixins.base import BaseMixin

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

    def check_path_exists(self, relative_path):
        cursor = self.conn.cursor()
        cursor.execute("SELECT id FROM pending_media WHERE file_path = ?", (relative_path,))
        if cursor.fetchone(): return True
        cursor.execute("SELECT id FROM activities WHERE photo_paths LIKE ?", (f'%{relative_path}%',))
        return cursor.fetchone() is not None
