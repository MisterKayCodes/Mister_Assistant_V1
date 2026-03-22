import os
import sys
import asyncio
import unittest
from datetime import datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

# Ensure root is in path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from bot.handlers import telegram_handler, help_handler, start_handler, repo
from utils.formatter import Formatter

class TestAllFeatures(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.user_id = 999
        self.fmt = Formatter()
        # Clean DB for user
        cursor = repo.conn.cursor()
        cursor.execute("DELETE FROM activities WHERE user_id = ?", (self.user_id,))
        cursor.execute("DELETE FROM spending WHERE user_id = ?", (self.user_id,))
        cursor.execute("DELETE FROM people WHERE user_id = ?", (self.user_id,))
        repo.conn.commit()

    def get_mock_msg(self, text):
        message = AsyncMock()
        message.from_user.id = self.user_id
        message.text = text
        message.caption = None
        message.answer = AsyncMock()
        message.reply = AsyncMock()
        return message

    async def test_01_activity_tracking(self):
        # Start
        msg = self.get_mock_msg("starting coding")
        await telegram_handler(msg)
        msg.answer.assert_called()
        self.assertIn("coding", msg.answer.call_args[0][0])

        # Status
        msg = self.get_mock_msg("what am i doing?")
        await telegram_handler(msg)
        self.assertIn("coding", msg.answer.call_args[0][0])

        # Stop
        msg = self.get_mock_msg("done")
        await telegram_handler(msg)
        self.assertIn("Stopped", msg.answer.call_args[0][0])

    async def test_02_historian_retro(self):
        # Range
        msg = self.get_mock_msg("i watched movie from 2pm to 4pm")
        await telegram_handler(msg)
        self.assertIn("Historically logged", msg.answer.call_args[0][0])
        self.assertIn("watched movie", msg.answer.call_args[0][0])

        # Conflict
        msg = self.get_mock_msg("i nap at 3pm")
        await telegram_handler(msg)
        self.assertIn("Conflict", msg.answer.call_args[0][0])

    async def test_03_finance_and_people(self):
        # Person
        msg = self.get_mock_msg("My sister is Chichi")
        await telegram_handler(msg)
        self.assertIn("Chichi", msg.answer.call_args[0][0])

        # Spend
        msg = self.get_mock_msg("spent 5000 on pizza")
        await telegram_handler(msg)
        self.assertIn("pizza", msg.answer.call_args[0][0])

    async def test_04_utilities(self):
        # Time
        msg = self.get_mock_msg("what time is it?")
        await telegram_handler(msg)
        self.assertIn("current time", msg.answer.call_args[0][0])

        # Help
        msg = self.get_mock_msg("/help")
        await help_handler(msg)
        self.assertIn("MANUAL", msg.answer.call_args[0][0])

if __name__ == "__main__":
    unittest.main()
