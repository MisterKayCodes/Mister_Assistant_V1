import sys
import asyncio
import logging
from aiogram import Bot, Dispatcher, types
from config import TELEGRAM_BOT_TOKEN
from bot.handlers import router, repo, engine # Import engine to inject scheduler
from services.scheduler_service import SchedulerService
from utils.logger import setup_logging

# Rule 10: Observability
setup_logging()
logger = logging.getLogger(__name__)

# Global Scheduler Instance (Dependency Injection)
scheduler: SchedulerService = None
from bot import session # Shared bot instance
# Repository is already imported from handlers, but we make it easier to reach
from bot.handlers import repo

async def reminder_scheduler(bot: Bot):
    """Background heartbeat for reminders (Rule 7: Resilience)"""
    logger.info("⏰ Reminder Heartbeat started.")
    while True:
        try:
            due = repo.get_due_reminders()
            for r_id, user_id, text in due:
                await bot.send_message(user_id, f"🔔 **REMINDER:** {text}")
                repo.mark_reminder_sent(r_id)
                logger.info(f"🔔 Sent reminder {r_id} to {user_id}")
        except Exception as e:
            logger.error(f"🚨 Heartbeat Error: {e}")
            
        await asyncio.sleep(60) # Check every minute

async def main():
    if not TELEGRAM_BOT_TOKEN:
        print("[!] TELEGRAM_BOT_TOKEN not found in .env file.")
        sys.exit(1)

    print("🤖 Mister Assistant Telegram Bot Starting...")
    session.bot = Bot(token=TELEGRAM_BOT_TOKEN)
    bot = session.bot # Local reference for convenience
    dp = Dispatcher()
    dp.include_router(router)
    
    # Initialize Scheduler (Senior Refinement)
    global scheduler
    scheduler = SchedulerService(bot, repo)
    scheduler.start()
    
    # Inject Scheduler into Engine (Dependency Injection Fix)
    engine.set_scheduler(scheduler)
    
    # Start the Heartbeat (The Alarm Clock)
    asyncio.create_task(reminder_scheduler(bot))
    
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
