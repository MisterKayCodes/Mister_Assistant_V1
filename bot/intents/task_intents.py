import json
import logging
import re
from datetime import datetime, timedelta
from aiogram import types
from utils.formatter import Formatter

logger = logging.getLogger(__name__)

class TaskIntents:
    def __init__(self, repo, fmt, logic, scheduler):
        self.repo = repo
        self.fmt = fmt
        self.logic = logic
        self.scheduler = scheduler

    async def intent_add_tasks(self, user_id, parsed):
        """Phase 4: The Mouth - Creating the session."""
        task_list = parsed.get("task_list")
        duration = parsed.get("duration_minutes")
        
        task_id = self.repo.add_task_group(user_id, task_list, duration)
        
        # Schedule reminders
        task = self.repo.get_task_by_id(task_id)
        self.scheduler.schedule_task_reminders(task_id, user_id, task['end_time'])
        
        # Format response
        end_time = datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S.%f")
        response = f"🦾 **TASK SESSION STARTED!**\n\n"
        response += f"📋 **Items:** {', '.join(task_list)}\n"
        response += f"⏳ **Duration:** {duration}m (Ends at {end_time.strftime('%H:%M')})\n\n"
        response += "I'll ping you 30 mins before the end to check your progress!"
        
        return self.fmt.format_success(response)

    async def intent_task_status(self, user_id, parsed):
        """Senior Refinement #2: Visual Status with Unicode Progress Bar."""
        task = self.repo.get_active_task_group(user_id)
        if not task:
            return self.fmt.format_info("You don't have an active task session right now. Use `Tasks: ... | Duration: ...` to start one!")

        start_time = datetime.strptime(task['start_time'], "%Y-%m-%d %H:%M:%S.%f")
        end_time = datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S.%f")
        now = datetime.now()
        
        total_sec = (end_time - start_time).total_seconds()
        elapsed_sec = (now - start_time).total_seconds()
        
        percent = min(100, max(0, int((elapsed_sec / total_sec) * 100)))
        
        # Helper: 10-block progress bar
        filled = round((percent / 100) * 10)
        bar = "▰" * filled + "▱" * (10 - filled)
        
        response = f"⏳ **CURRENT SESSION**\n"
        response += f"[{bar}] {percent}%\n"
        response += f"🏁 **Ends at:** {end_time.strftime('%H:%M')} ({int((end_time - now).total_seconds() // 60)}m left)\n\n"
        
        tasks = json.loads(task['task_list'])
        completed_indices = json.loads(task['completed_indices'] or "[]")
        
        response += "📋 **Tasks:**\n"
        for i, t in enumerate(tasks):
            icon = "✅" if i in completed_indices else "◽"
            response += f"{icon} {i+1}. {t}\n"
            
        return self.fmt.format_info(response)

    async def intent_task_history(self, user_id, parsed):
        """Phase 4: Historical Lookup."""
        history = self.repo.get_task_history(user_id)
        if not history:
            return self.fmt.format_info("No task history found yet. Complete a session to see it here!")

        response = "📜 **PRODUCTIVITY HISTORY**\n\n"
        for entry in history:
            date_str = datetime.strptime(entry['created_at'], "%Y-%m-%d %H:%M:%S").strftime("%b %d, %H:%M")
            original = json.loads(entry['original_task_list'])
            completed = json.loads(entry['completed_items'])
            
            response += f"📅 **{date_str}**\n"
            response += f"✅ Finished: {len(completed)}/{len(original)} items\n"
            if entry['notes']:
                response += f"📝 Note: {entry['notes']}\n"
            response += "---\n"
            
        return self.fmt.format_info(response)

    async def handle_callback(self, callback_query: types.CallbackQuery):
        """Senior Refinement #1 & #3: Interactive Handlers & Sync Snooze."""
        data = callback_query.data
        user_id = str(callback_query.from_user.id)
        
        if data.startswith("task_done:"):
            task_id = int(data.split(":")[1])
            task = self.repo.get_task_by_id(task_id)
            if task:
                self.repo.update_task_status(task_id, status='completed', completed_indices=list(range(len(json.loads(task['task_list'])))))
                # Log it
                tasks = json.loads(task['task_list'])
                self.repo.log_task_completion(task_id, user_id, tasks, tasks, "Marked as 'All Done' via button.")
                await callback_query.message.edit_text("✅ All tasks marked as completed! Great job! 🦾")
            
        elif data.startswith("task_snooze:"):
            task_id = int(data.split(":")[1])
            task = self.repo.get_task_by_id(task_id)
            if task:
                # Senior Refinement #3: Sync Snooze
                current_end = datetime.strptime(task['end_time'], "%Y-%m-%d %H:%M:%S.%f")
                new_end = current_end + timedelta(minutes=15)
                self.scheduler.reschedule_task(task_id, user_id, new_end)
                await callback_query.message.edit_text(f"⏳ Snoozed! End time pushed to {new_end.strftime('%H:%M')}.")

        elif data.startswith("task_cancel:"):
            task_id = int(data.split(":")[1])
            self.repo.update_task_status(task_id, status='failed')
            await callback_query.message.edit_text("❌ Task session cancelled.")

        await callback_query.answer()

    async def handle_validation(self, message: types.Message, user_id, text, task):
        """Batch validation (Senior Refinement #2)."""
        task_list = json.loads(task['task_list'])
        completed_indices = []
        
        if text.lower() == 'all':
            completed_indices = list(range(len(task_list)))
        else:
            # Extract numbers
            nums = re.findall(r"\d+", text)
            for n in nums:
                idx = int(n) - 1
                if 0 <= idx < len(task_list):
                    completed_indices.append(idx)
                    
        if not completed_indices:
            await message.answer("I didn't catch which tasks you finished. Please send numbers like `1, 2` or `all`. You can also include a note.")
            return

        completed_items = [task_list[i] for i in completed_indices]
        notes = text.replace('all', '').strip()
        # Remove the numbers from notes if they were just indices
        for n in nums: notes = notes.replace(n, '').strip()
        notes = re.sub(r"[,;.]", "", notes).strip()

        self.repo.update_task_status(task['id'], status='completed' if len(completed_indices) == len(task_list) else 'partial', completed_indices=completed_indices)
        self.repo.log_task_completion(task['id'], user_id, completed_items, task_list, notes or "No specific notes.")
        
        self.repo.update_user_state(user_id, state_context=None)
        
        response = f"✅ **LOGGED!**\n\nFinished: {', '.join(completed_items)}\n"
        if notes: response += f"📝 **Note:** {notes}"
        
        await message.answer(self.fmt.format_success(response), parse_mode="Markdown")
