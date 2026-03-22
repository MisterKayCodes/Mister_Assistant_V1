import json
import dateparser
from datetime import timedelta, datetime
from aiogram import types

class ActivityIntents:
    def __init__(self, repo, fmt, logic):
        self.repo = repo
        self.fmt = fmt
        self.logic = logic

    async def handle_caption(self, message, uid, text, parser):
        parsed = parser.parse(text)
        if parsed and parsed.get("intent") in ["retro_log", "retro_log_start_only"]:
            name, start = parsed.get("name"), parsed.get("start")
            end = parsed.get("end") or (start + timedelta(hours=1))
            conflicts = self.repo.check_for_conflicts(uid, start, end)
            if conflicts:
                await message.reply(f"⚠️ **Conflict:** `{conflicts[0]['name']}` is there.")
                return
            photos = self.repo.get_pending_media(uid)
            self.repo.log_retro_activity(uid, name, start, end, photos)
            self.repo.clear_pending_media(uid)
            self.repo.update_user_state(uid, state_context=None)
            await message.answer(f"✅ Logged with photos: **{name}**")
        else:
            self.repo.complete_activity_with_media(uid, text)
            await message.answer(f"✅ Logged: **{text}**")

    async def handle_correction_selection(self, message, uid, text, state):
        try:
            choice = int(text.strip()) - 1
            raw_opts = state.get("correction_options")
            options = json.loads(raw_opts) if isinstance(raw_opts, str) else (raw_opts or [])
            if 0 <= choice < len(options):
                target = options[choice]
                raw_info = state.get("correction_new_info")
                new_info = json.loads(raw_info) if isinstance(raw_info, str) else (raw_info or {})
                res = self.repo.update_activity(target["id"], name=new_info.get("name"))
                if res["status"] == "success":
                    await message.answer(self.fmt.format_correction_diff(res["old"], res["new"]), parse_mode="Markdown")
                else:
                    await message.answer(self.fmt.format_error("Conflict!"))
                self.repo.update_user_state(uid, state_context=None, correction_options=None, correction_new_info=None)
            else:
                await message.answer("Invalid choice.")
        except Exception as e:
            await message.answer(f"Please send a number. (Err: {type(e).__name__})")

    async def handle_deletion_selection(self, message, uid, text, state):
        try:
            choice = int(text.strip()) - 1
            raw_opts = state.get("correction_options")
            options = json.loads(raw_opts) if isinstance(raw_opts, str) else (raw_opts or [])
            if 0 <= choice < len(options):
                target = options[choice]
                self.repo.delete_activity(target["id"])
                await message.answer(self.fmt.format_success(f"🗑️ Deleted: **{target['name']}**"), parse_mode="Markdown")
                self.repo.update_user_state(uid, state_context=None, correction_options=None)
            else:
                await message.answer("Invalid choice.")
        except Exception as e:
            await message.answer(f"Please send a number. (Selection Err: {type(e).__name__})")

    async def intent_start(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        if aid: self.repo.stop_activity(aid)
        self.repo.start_activity(uid, p.get("name"))
        return self.fmt.format_success(self.logic.format_start_message(p.get("name")))

    async def intent_stop(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        if not aid: return self.fmt.format_error("Not tracking.")
        duration = self.repo.stop_activity(aid)
        self.repo.update_user_state(uid, current_activity_id=None)
        return self.fmt.format_success(self.logic.format_stop_message(duration))

    async def intent_switch(self, uid, p):
        aid = self.repo.get_active_activity(uid)
        dur = self.repo.stop_activity(aid) if aid else None
        self.repo.start_activity(uid, p.get("name"))
        return self.fmt.format_success(self.logic.format_switch_message(dur, p.get("name")))

    async def intent_correction(self, uid, p):
        dt = dateparser.parse(p.get("time_str"), settings={'PREFER_DATES_FROM': 'past'})
        if not dt: return self.fmt.format_error("Unknown time.")
        matches = self.repo.find_activities_at_time(uid, dt.isoformat())
        if not matches: return self.fmt.format_error(f"Nothing at {dt.strftime('%H:%M')}.")
        if len(matches) == 1:
            res = self.repo.update_activity(matches[0]["id"], name=p.get("new_name"))
            return self.fmt.format_correction_diff(res["old"], res["new"]) if res["status"] == "success" else self.fmt.format_error("Conflict!")
        
        self.repo.update_user_state(uid, state_context="WAITING_FOR_CORRECTION_SELECTION", correction_options=json.dumps(matches), correction_new_info=json.dumps({"name": p.get("new_name")}))
        return self.fmt.format_selection_menu(matches, dt.strftime("%H:%M"))

    async def intent_delete(self, uid, p):
        time_str, name = p.get("time_str"), p.get("name")
        if time_str:
            dt = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'past'})
            if not dt: return self.fmt.format_error("Unknown time.")
            matches = self.repo.find_activities_at_time(uid, dt.isoformat())
        else:
            cursor = self.repo.conn.cursor()
            cursor.execute("SELECT id, name, start_time FROM activities WHERE user_id = ? AND name LIKE ? ORDER BY start_time DESC LIMIT 5", (uid, f"%{name}%"))
            matches = [{"id": row[0], "name": row[1], "start": row[2]} for row in cursor.fetchall()]

        if not matches: return self.fmt.format_error("Nothing to delete.")
        if len(matches) == 1:
            self.repo.delete_activity(matches[0]["id"])
            return self.fmt.format_success(f"🗑️ Deleted: **{matches[0]['name']}**")
        
        self.repo.update_user_state(uid, state_context="WAITING_FOR_DELETION_SELECTION", correction_options=json.dumps(matches))
        return self.fmt.format_info("🧐 Multiple matches? Which to delete?\n\n" + "\n".join([f"{i+1}. {m['name']} ({m.get('start', '?')})" for i, m in enumerate(matches)]))
    async def intent_retro_log(self, uid, p):
        name, start, end = p.get("name"), p.get("start"), p.get("end")
        conflicts = self.repo.check_for_conflicts(uid, start, end)
        if conflicts: return self.fmt.format_error(f"Conflict with `{conflicts[0]['name']}`.")
        self.repo.log_retro_activity(uid, name, start, end)
        date_str = start.strftime("%b %d")
        return self.fmt.format_success(f"Logged 🕰️ **{name}** on {date_str} from {start.strftime('%H:%M')} to {end.strftime('%H:%M')}")

    async def intent_retro_log_start_only(self, uid, p):
        name, start = p.get("name"), p.get("start")
        # Ensure it's not logging today if the user said yesterday
        end = start + timedelta(hours=1) 
        conflicts = self.repo.check_for_conflicts(uid, start, end)
        if conflicts: return self.fmt.format_error(f"Conflict with `{conflicts[0]['name']}`.")
        self.repo.log_retro_activity(uid, name, start, end)
        date_str = start.strftime("%b %d")
        return self.fmt.format_success(f"Logged 🕰️ **{name}** for {date_str} at {start.strftime('%H:%M')} (1h block)")
