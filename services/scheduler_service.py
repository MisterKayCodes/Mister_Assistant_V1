import logging
import json
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
from datetime import datetime, timedelta
from config import DB_PATH

logger = logging.getLogger(__name__)

class SchedulerService:
    def __init__(self, bot, repo):
        self.bot = bot
        self.repo = repo
        
        # Rule 1: Persistent Job Store (The Reboot Problem)
        jobstores = {
            'default': SQLAlchemyJobStore(url=f'sqlite:///{DB_PATH}')
        }
        
        # Rule 1: Misfire Protection (Zombified Task Filter)
        job_defaults = {
            'misfire_grace_time': 300, # 5 minutes
            'coalesce': True,
            'max_instances': 1
        }
        
        self.scheduler = AsyncIOScheduler(jobstores=jobstores, job_defaults=job_defaults)

    def start(self):
        if not self.scheduler.running:
            self.scheduler.start()
            logger.info("⏰ Scheduler Service Started.")

    def schedule_task_reminders(self, task_id, user_id, end_time_str):
        """Schedules the 30-minute warning and the final check."""
        # Convert string to datetime if needed
        if isinstance(end_time_str, str):
            end_time = datetime.strptime(end_time_str, "%Y-%m-%d %H:%M:%S.%f")
        else:
            end_time = end_time_str
            
        warning_time = end_time - timedelta(minutes=30)
        
        # Job 1: 30-Minute Warning
        self.scheduler.add_job(
            self.send_task_warning,
            'date',
            run_date=warning_time,
            args=[task_id, user_id],
            id=f"warn_{task_id}",
            replace_existing=True
        )
        
        # Job 2: Final Check
        self.scheduler.add_job(
            self.send_final_check,
            'date',
            run_date=end_time,
            args=[task_id, user_id],
            id=f"final_{task_id}",
            replace_existing=True
        )
        
        logger.info(f"📅 Scheduled reminders for Task {task_id} (User: {user_id})")

    async def send_task_warning(self, task_id, user_id):
        """Sends an interactive warning with Inline Buttons."""
        from bot.keyboards import get_task_warning_keyboard
        task = self.repo.get_task_by_id(task_id)
        if not task or task['status'] != 'pending':
            return

        text = "🔔 **30 MINUTE WARNING!**\n\nYour time is almost up. Are you done with your tasks?\n\n"
        tasks = json.loads(task['task_list'])
        for i, t in enumerate(tasks):
            text += f"{i+1}. {t}\n"
            
        await self.bot.send_message(
            user_id, 
            text, 
            reply_markup=get_task_warning_keyboard(task_id),
            parse_mode="Markdown"
        )
        # Update state to prepare for validation
        self.repo.update_user_state(str(user_id), state_context="WAITING_FOR_TASK_LOG")

    async def send_final_check(self, task_id, user_id):
        """Sends the final completion check message."""
        task = self.repo.get_task_by_id(task_id)
        if not task or task['status'] != 'pending':
            return

        text = "🏁 **TIME IS UP!**\n\nHow did it go? Send the numbers of the tasks you finished (e.g. `1, 3`) or type `all` if you're a beast! 🦾"
        await self.bot.send_message(user_id, text, parse_mode="Markdown")
        self.repo.update_user_state(str(user_id), state_context="WAITING_FOR_TASK_LOG")

    def reschedule_task(self, task_id, user_id, new_end_time):
        """Snooze logic: Updates DB and Jobs."""
        # 1. Update Scheduler
        self.schedule_task_reminders(task_id, user_id, new_end_time)
        # 2. Update DB (Safety Guard #3)
        self.repo.update_task_status(task_id, status='pending', end_time=new_end_time)
        logger.info(f"⏳ Snoozed Task {task_id} to {new_end_time}")

import json # Late import to avoid edge cases in job serialization if any
