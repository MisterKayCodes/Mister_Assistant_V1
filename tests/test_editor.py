import unittest
from datetime import datetime, timedelta
import os
import sqlite3
import sys

# Ensure root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import config BEFORE repo to override
import config
TEST_DB = "tests/test_editor.db"
config.DB_PATH = TEST_DB

from data.repository import Repository

class TestEditor(unittest.TestCase):
    def setUp(self):
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
                if os.path.exists(TEST_DB + "-wal"): os.remove(TEST_DB + "-wal")
                if os.path.exists(TEST_DB + "-shm"): os.remove(TEST_DB + "-shm")
            except: pass
        
        self.repo = Repository()

    def tearDown(self):
        self.repo.conn.close()
        if os.path.exists(TEST_DB):
            try:
                os.remove(TEST_DB)
                if os.path.exists(TEST_DB + "-wal"): os.remove(TEST_DB + "-wal")
                if os.path.exists(TEST_DB + "-shm"): os.remove(TEST_DB + "-shm")
            except: pass

    def test_surgical_update_integrity(self):
        """Rule 1: Update must re-check conflicts."""
        uid = "user1"
        # Use datetime objects
        d1_s = datetime(2026, 3, 22, 6, 0)
        d1_e = datetime(2026, 3, 22, 7, 0)
        d2_s = datetime(2026, 3, 22, 8, 0)
        d2_e = datetime(2026, 3, 22, 8, 30)
        
        # 1. Log two separate activities
        self.repo.log_retro_activity(uid, "Gym", d1_s, d1_e)
        self.repo.log_retro_activity(uid, "Breakfast", d2_s, d2_e)
        
        # Find Gym ID
        check_time = datetime(2026, 3, 22, 6, 30).isoformat()
        matches = self.repo.find_activities_at_time(uid, check_time)
        self.assertTrue(len(matches) > 0)
        gym_id = matches[0]["id"]
        
        # 2. Try to expand Gym to overlap Breakfast (6am to 9am)
        # update_activity accepts strings for times (which we pass to DB)
        res = self.repo.update_activity(gym_id, end=datetime(2026, 3, 22, 9, 0).isoformat())
        
        # Must fail with conflict
        self.assertEqual(res["status"], "conflict")
        self.assertEqual(res["conflicts"][0]["name"], "Breakfast")

    def test_ambiguity_selection(self):
        """Rule 10: Find multiple activities at once."""
        uid = "user1"
        # Two overlapping events
        # A: 5:50 - 6:10
        # B: 6:00 - 7:00
        self.repo.log_retro_activity(uid, "Snack", datetime(2026, 3, 22, 5, 50), datetime(2026, 3, 22, 6, 10))
        self.repo.log_retro_activity(uid, "Gym", datetime(2026, 3, 22, 6, 0), datetime(2026, 3, 22, 7, 0))
        
        check_time = datetime(2026, 3, 22, 6, 5).isoformat()
        matches = self.repo.find_activities_at_time(uid, check_time)
        self.assertEqual(len(matches), 2)
        match_names = [m["name"] for m in matches]
        self.assertIn("Snack", match_names)
        self.assertIn("Gym", match_names)

if __name__ == "__main__":
    unittest.main()
