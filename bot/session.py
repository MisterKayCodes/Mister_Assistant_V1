from aiogram import Bot

# Global bot instance to avoid pickling/circular import issues
bot: Bot = None
