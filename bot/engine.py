import random
import json
import dateparser
from aiogram import types
from datetime import timedelta, datetime
from core.analytics import AnalyticsEngine
from core.parser import Parser
from core.logic import Logic
from data.repository import Repository
from services.media_manager import MediaManager
from utils.formatter import Formatter

class ResponseEngine:
    def __init__(self, db_path):
        self.parser = Parser()
        self.logic = Logic()
        self.repo = Repository()
        self.manager = MediaManager()
        self.fmt = Formatter()
        self.analytics = AnalyticsEngine(db_path)

    async def handle_message(self, message: types.Message):
        user_id = str(message.from_user.id)
        text = message.text or message.caption 
        if not text: return

        # --- Escape Hatch ---
        if text.startswith("/") and text not in ["/start", "/help"]:
            self.repo.clear_pending_media(user_id)
            self.repo.update_user_state(user_id, state_context=None)
            await message.answer(self.fmt.format_info("Action cancelled." if text == "/cancel" else "Command received. Photo session cleared."))
            return

        state = self.repo.get_user_state(user_id)
        context = state.get("state_context")

        # --- Dispatch State Handlers ---
        if context == "WAITING_FOR_CAPTION":
            await self._handle_caption(message, user_id, text)
        elif context == "WAITING_FOR_CORRECTION_SELECTION":
            await self._handle_correction_selection(message, user_id, text, state)
        elif context == "WAITING_FOR_RESET_CODE":
            await self._handle_reset_confirmation(message, user_id, text, state)
        else:
            await self._handle_intent(message, user_id, text)

    async def _handle_caption(self, message, user_id, text):
        parsed = self.parser.parse(text)
        if parsed and parsed.get("intent") in ["retro_log", "retro_log_start_only"]:
            name = parsed.get("name")
            start = parsed.get("start")
            end = parsed.get("end") or (start + timedelta(hours=1))
            conflicts = self.repo.check_for_conflicts(user_id, start, end)
            if conflicts:
                await message.reply(f"⚠️ **Temporal Conflict!** You were already doing `{conflicts[0]}` at that time.")
                return
            photos = self.repo.get_pending_media(user_id)
            self.repo.log_retro_activity(user_id, name, start, end, photos)
            self.repo.clear_pending_media(user_id)
            self.repo.update_user_state(user_id, state_context=None)
            await message.answer(f"✅ Historically logged: **{name}** ({start.strftime('%H:%M')} - {end.strftime('%H:%M')})")
        else:
            self.repo.complete_activity_with_media(user_id, text)
            await message.answer(f"✅ Activity logged with visual evidence: **{text}**")

    async def _handle_correction_selection(self, message, user_id, text, state):
        try:
            choice = int(text.strip()) - 1
            options = json.loads(state.get("correction_options", "[]"))
            if 0 <= choice < len(options):
                target = options[choice]
                new_info = json.loads(state.get("correction_new_info", "{}"))
                res = self.repo.update_activity(target["id"], name=new_info.get("name"))
                if res["status"] == "success":
                    await message.answer(self.fmt.format_correction_diff(res["old"], res["new"]), parse_mode="Markdown")
                else:
                    await message.answer(self.fmt.format_error("Conflict detected!"))
                self.repo.update_user_state(user_id, state_context=None, correction_options=None, correction_new_info=None)
            else:
                await message.answer("Invalid choice. Send number or /cancel.")
        except:
            await message.answer("Please send a number.")

    async def _handle_reset_confirmation(self, message, user_id, text, state):
        if text.strip() == str(state.get("reset_code")):
            self.repo.clear_all_user_data(user_id)
            self.repo.update_user_state(user_id, state_context=None, reset_code=None)
            await message.answer(self.fmt.format_success("DATABASE WIPED. 👻"))
        else:
            self.repo.update_user_state(user_id, state_context=None, reset_code=None)
            await message.answer(self.fmt.format_error("Reset cancelled."))

    async def _handle_intent(self, message, user_id, text):
        parsed = self.parser.parse(text)
        if not parsed:
            await message.answer(self.logic.format_unknown())
            return

        intent = parsed.get("intent")
        response = ""
        # ... logic for each intent (start, stop, etc.)
        # To keep THIS file under 200, I'll move intent dispatching to a dict or small methods
        handler_name = f"_intent_{intent}"
        if hasattr(self, handler_name):
            response = await getattr(self, handler_name)(user_id, parsed)
        else:
            response = self.logic.format_unknown()

        if response:
            await message.answer(response, parse_mode="Markdown")

    async def _intent_start_activity(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        if aid: self.repo.stop_activity(aid)
        self.repo.start_activity(uid, p.get("name"))
        return self.fmt.format_success(self.logic.format_start_message(p.get("name")))

    async def _intent_stop_activity(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        if not aid: return self.fmt.format_error("Not tracking.")
        duration = self.repo.stop_activity(aid)
        self.repo.update_user_state(uid, current_activity_id=None)
        return self.fmt.format_success(self.logic.format_stop_message(duration))

    async def _intent_switch_activity(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        dur = self.repo.stop_activity(aid) if aid else None
        self.repo.start_activity(uid, p.get("name"))
        return self.fmt.format_success(self.logic.format_switch_message(dur, p.get("name")))

    async def _intent_log_spending(self, uid, p):
        self.repo.log_spending(uid, p.get("amount"), p.get("category"))
        return self.fmt.format_success(self.logic.format_spending_logged(p.get("amount"), p.get("category")))

    async def _intent_correction(self, uid, p):
        dt = dateparser.parse(p.get("time_str"), settings={'PREFER_DATES_FROM': 'past'})
        if not dt: return self.fmt.format_error("Unknown time.")
        matches = self.repo.find_activities_at_time(uid, dt.isoformat())
        if not matches: return self.fmt.format_error(f"Nothing at {dt.strftime('%H:%M')}.")
        if len(matches) == 1:
            res = self.repo.update_activity(matches[0]["id"], name=p.get("new_name"))
            return self.fmt.format_correction_diff(res["old"], res["new"]) if res["status"] == "success" else self.fmt.format_error("Conflict!")
        
        self.repo.update_user_state(
            uid, 
            state_context="WAITING_FOR_CORRECTION_SELECTION", 
            correction_options=json.dumps(matches), 
            correction_new_info=json.dumps({"name": p.get("new_name")})
        )
        return self.fmt.format_selection_menu(matches, dt.strftime("%H:%M"))

    async def _intent_add_person(self, uid, p):
        self.repo.add_person(uid, p.get("name"), p.get("relationship"))
        return self.fmt.format_success(self.logic.format_person_added(p.get("name"), p.get("relationship")))

    async def _intent_check_activity(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        if aid:
            name = self.repo.get_activity_name(aid)
            return self.fmt.format_info(self.logic.format_check_message(name))
        return self.fmt.format_error("Not tracking.")

    async def _intent_retro_log(self, uid, p):
        start, end, name = p.get("start"), p.get("end"), p.get("name")
        conflicts = self.repo.check_for_conflicts(uid, start, end)
        if conflicts:
            return self.fmt.format_error(f"**Conflict:** `{conflicts[0]['name']}` is there.")
        self.repo.log_retro_activity(uid, name, start, end)
        return self.fmt.format_success(f"Logged: **{name}** ({start.strftime('%H:%M')} - {end.strftime('%H:%M')})")

    async def _intent_retro_log_start_only(self, uid, p):
        start, name = p.get("start"), p.get("name")
        end = start + timedelta(hours=1)
        conflicts = self.repo.check_for_conflicts(uid, start, end)
        if conflicts:
            return self.fmt.format_error(f"**Conflict:** `{conflicts[0]['name']}` exists.")
        self.repo.log_retro_activity(uid, name, start, end)
        return self.fmt.format_success(f"Logged: **{name}** at {start.strftime('%H:%M')} (1hr).")

    async def _intent_reset_request(self, uid, p):
        code = random.randint(1000, 9999)
        self.repo.update_user_state(uid, state_context="WAITING_FOR_RESET_CODE", reset_code=code)
        return self.fmt.format_error(f"**NUCLEAR RESET**\nSend code: `{code}`")

    async def _intent_tell_time(self, uid, p):
        now = datetime.now()
        return f"🕒 Current time: **{now.strftime('%H:%M:%S')}** (UTC+1)."

    async def _intent_set_reminder(self, uid, p):
        self.repo.set_reminder(uid, p.get("text"), p.get("time"))
        return self.logic.format_reminder_set(p.get("text"), p.get("friendly_time") or p.get("time"))
