import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN
from bot.handlers import router
from utils.logger import setup_logging

# Rule 10: Observability
setup_logging()
logger = logging.getLogger(__name__)

async def main():
    if not TELEGRAM_BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN not found in .env file.")
        sys.exit(1)

    print("🤖 Mister Assistant Telegram Bot Starting...")
    bot = Bot(token=TELEGRAM_BOT_TOKEN)
    dp = Dispatcher()
    dp.include_router(router)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        print(f"[!] Error: {e}")
    finally:
        await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n[!] Bot stopped by user.")
