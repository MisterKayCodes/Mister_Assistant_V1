from datetime import datetime
import random

class SystemIntents:
    def __init__(self, repo, fmt, logic, analytics):
        self.repo = repo
        self.fmt = fmt
        self.logic = logic
        self.analytics = analytics

    async def handle_reset_confirmation(self, message, uid, text, state):
        if text.strip() == str(state.get("reset_code")):
            self.repo.clear_all_user_data(uid)
            self.repo.update_user_state(uid, state_context=None, reset_code=None)
            await message.answer(self.fmt.format_success("DATABASE WIPED. 👻"))
        else:
            self.repo.update_user_state(uid, state_context=None, reset_code=None)
            await message.answer(self.fmt.format_error("Reset cancelled."))

    async def intent_summary(self, uid, p):
        report = self.analytics.get_summary(uid, period=p.get("period"))
        return self.fmt.format_summary(report)

    async def intent_reset_request(self, uid, p):
        code = random.randint(1000, 9999)
        self.repo.update_user_state(uid, state_context="WAITING_FOR_RESET_CODE", reset_code=code)
        return self.fmt.format_error(f"**NUCLEAR RESET**\nSend code: `{code}`")

    async def intent_tell_time(self, uid, p):
        now = datetime.now()
        return f"🕒 Current time: **{now.strftime('%H:%M:%S')}** (UTC+1)."

    async def intent_set_reminder(self, uid, p):
        self.repo.set_reminder(uid, p.get("text"), p.get("time"))
        return self.logic.format_reminder_set(p.get("text"), p.get("friendly_time") or p.get("time"))
