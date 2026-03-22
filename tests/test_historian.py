import os
import sys
import asyncio
import unittest
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock
from bot.handlers import telegram_handler, photo_handler, repo

class TestHistorian(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.user_id = "123456"
        # Reset DB state for user
        repo.clear_pending_media(self.user_id)
        repo.update_user_state(self.user_id, state_context=None)
        # Clear activities for user to ensure clean start
        conn = repo.conn
        conn.execute("DELETE FROM activities WHERE user_id = ?", (self.user_id,))
        conn.commit()

    async def test_retro_log_range(self):
        # "i watched movie from 2pm to 4pm"
        message = AsyncMock()
        message.from_user.id = self.user_id
        message.text = "i watched movie from 2pm to 4pm"
        message.caption = None
        message.answer = AsyncMock()

        await telegram_handler(message)
        
        # Verify DB
        cursor = repo.conn.cursor()
        cursor.execute("SELECT name, start_time, end_time, duration FROM activities WHERE user_id = ?", (self.user_id,))
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(row[0], "watched movie")
        # Check if it was today at 14:00 and 16:00
        start = datetime.fromisoformat(row[1])
        end = datetime.fromisoformat(row[2])
        self.assertEqual(start.hour, 14)
        self.assertEqual(end.hour, 16)
        self.assertEqual(row[3], 7200)

    async def test_conflict_detection(self):
        # 1. Log movie 2-4pm
        await self.test_retro_log_range()
        
        # 2. Try to log nap at 3pm
        message = AsyncMock()
        message.from_user.id = self.user_id
        message.text = "i nap at 3pm"
        message.answer = AsyncMock()

        await telegram_handler(message)
        
        # Verify error message sent
        message.answer.assert_called()
        args = message.answer.call_args[0][0]
        self.assertIn("Conflict", args)
        self.assertIn("watched movie", args)

    async def test_multimodal_retro(self):
        # 1. Send photo
        p_message = AsyncMock()
        p_message.from_user.id = self.user_id
        p_message.photo = [MagicMock(file_id="mock_file")]
        p_message.bot = MagicMock()
        # Mock media manager to return a path
        from services.media_manager import MediaManager
        MediaManager.save_photo = AsyncMock(return_value="media/test.jpg")
        
        await photo_handler(p_message)
        
        # 2. Caption it "i ate breakfast at 8am"
        c_message = AsyncMock()
        c_message.from_user.id = self.user_id
        c_message.text = "i ate breakfast at 8am"
        c_message.caption = None
        c_message.answer = AsyncMock()
        
        await telegram_handler(c_message)
        
        # Verify DB
        cursor = repo.conn.cursor()
        cursor.execute("SELECT name, start_time, photo_paths FROM activities WHERE name = 'ate breakfast'")
        row = cursor.fetchone()
        self.assertIsNotNone(row)
        self.assertEqual(datetime.fromisoformat(row[1]).hour, 8)
        self.assertIn("media/test.jpg", row[2])

if __name__ == "__main__":
    unittest.main()
