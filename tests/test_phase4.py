import unittest
from datetime import datetime, timedelta
import os
import sqlite3
import sys
# Ensure root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from core.analytics import AnalyticsEngine

class TestPhase4(unittest.TestCase):
    def setUp(self):
        self.db_path = "tests/test_phase4.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
        self.conn = sqlite3.connect(self.db_path)
        self.conn.execute("CREATE TABLE activities (user_id TEXT, name TEXT, start_time TEXT, end_time TEXT)")
        self.engine = AnalyticsEngine(self.db_path)

    def tearDown(self):
        self.conn.close()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_midnight_split(self):
        """Rule 1: If I sleep from 10pm to 6am, Today's summary only shows 6h."""
        user_id = "user1"
        # 10 PM Yesterday to 6 AM Today
        yesterday = (datetime.now() - timedelta(days=1)).replace(hour=22, minute=0, second=0, microsecond=0)
        today_6am = datetime.now().replace(hour=6, minute=0, second=0, microsecond=0)
        
        self.conn.execute(
            "INSERT INTO activities VALUES (?, ?, ?, ?)",
            (user_id, "Sleep", yesterday.isoformat(), today_6am.isoformat())
        )
        self.conn.commit()
        
        summary = self.engine.get_summary(user_id, period="today")
        # Should be exactly 6 hours (21600 seconds)
        self.assertEqual(summary["data"].get("Sleep"), 6 * 3600)

    def test_normalization(self):
        """Rule 2: 'Gym' and 'gym' should be merged."""
        user_id = "user1"
        now = datetime.now()
        start1 = now - timedelta(hours=2)
        end1 = now - timedelta(hours=1)
        start2 = now - timedelta(minutes=30)
        end2 = now
        
        self.conn.execute("INSERT INTO activities VALUES (?, ?, ?, ?)", (user_id, "Gym", start1.isoformat(), end1.isoformat()))
        self.conn.execute("INSERT INTO activities VALUES (?, ?, ?, ?)", (user_id, "gym", start2.isoformat(), end2.isoformat()))
        self.conn.commit()
        
        summary = self.engine.get_summary(user_id, period="today")
        # Should be 1h + 30m = 1.5h (5400 seconds)
        self.assertEqual(summary["data"].get("Gym"), 5400)

    def test_empty_state(self):
        """Rule 4: Handle zero state gracefully."""
        summary = self.engine.get_summary("ghost_user", period="today")
        self.assertEqual(len(summary["data"]), 0)
        self.assertEqual(summary["total_seconds"], 0)

if __name__ == "__main__":
    unittest.main()
