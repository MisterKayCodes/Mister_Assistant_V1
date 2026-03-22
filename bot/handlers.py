from aiogram import Router, types, F
from aiogram.filters import Command
from datetime import timedelta, datetime
import random
from config import DB_PATH
from core.analytics import AnalyticsEngine
from core.parser import Parser
from core.logic import Logic
from data.repository import Repository
from services.media_manager import MediaManager
from utils.formatter import Formatter

router = Router()
parser = Parser()
logic = Logic()
repo = Repository()
manager = MediaManager()
fmt = Formatter()
analytics = AnalyticsEngine(DB_PATH)

@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(fmt.format_help(), parse_mode="Markdown")

@router.message(Command("summary"))
async def summary_command_handler(message: types.Message):
    user_id = str(message.from_user.id)
    report = analytics.get_summary(user_id, period="today")
    await message.answer(fmt.format_summary(report), parse_mode="Markdown")

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    repo.clear_pending_media(user_id)
    repo.update_user_state(user_id, state_context=None)
    await message.answer(
        fmt.format_success("MISTER ASSISTANT: PHASE 3 ONLINE! 🦾\n\nI am your Personal Historian. Send `/help` to see my full capabilities."),
        parse_mode="Markdown"
    )

# --- NEW PHOTO HANDLER (The Ears) ---
@router.message(F.photo)
async def photo_handler(message: types.Message):
    user_id = str(message.from_user.id)
    state = repo.get_user_state(user_id)
    pending_before = repo.get_pending_media(user_id)
    
    # 1. Nervous System (Service) saves the file
    path = await manager.save_photo(message.bot, message.photo[-1], user_id)
    
    # 2. Vault (Data) records the pending file
    repo.add_pending_media(user_id, path)
    
    # 3. Check State for "Quiet Mode" (Rule 6: Resilience)
    # If this is the FIRST photo in the current pending queue, always reply with text
    # Even if state is stuck in WAITING_FOR_CAPTION
    if state.get("state_context") == "WAITING_FOR_CAPTION" and len(pending_before) > 0:
        # Rule 10: Observability (Acknowledging additional photos)
        try:
            await message.react([types.ReactionTypeEmoji(emoji="📥")])
        except:
            pass 
    else:
        # Initial greeting / Fresh session
        repo.update_user_state(user_id, state_context="WAITING_FOR_CAPTION")
        await message.reply("📸 I've saved the photo! What activity is this for? (Or send more photos)")

# --- UPDATED TEXT HANDLER (The Mouth) ---
@router.message()
async def telegram_handler(message: types.Message):
    user_id = str(message.from_user.id)
    # Teacher's Tip: Use .text OR .caption to catch everything
    text = message.text or message.caption 
    
    if not text:
        return

    # --- Escape Hatch (Rule 6: Resilience) ---
    if text.startswith("/") and text not in ["/start", "/help"]:
        repo.clear_pending_media(user_id)
        repo.update_user_state(user_id, state_context=None)
        if text == "/cancel":
            await message.answer(fmt.format_info("Action cancelled. Photo queue cleared."))
        else:
            await message.answer(fmt.format_info("Command received. Photo session cleared."))
        return

    # --- State Machine: WAITING_FOR_CAPTION ---
    state = repo.get_user_state(user_id)
    if state.get("state_context") == "WAITING_FOR_CAPTION":
        # Rule 5: Idempotency / JSON Serialization handled in Repo
        # Senior Check: Does the caption have a retro-time?
        parsed_caption = parser.parse(text) # Let the parser detect (i) optional
        if parsed_caption and parsed_caption.get("intent") in ["retro_log", "retro_log_start_only"]:
            # Multimodal Retro-Log logic
            name = parsed_caption.get("name")
            start = parsed_caption.get("start")
            end = parsed_caption.get("end") or (start + timedelta(hours=1))
            
            conflicts = repo.check_for_conflicts(user_id, start, end)
            if conflicts:
                await message.reply(f"⚠️ **Temporal Conflict!** You were already doing `{conflicts[0]}` at that time. Should I overwrite it (coming soon) or skip?")
                return
            
            # Log with photos
            photos = repo.get_pending_media(user_id)
            repo.log_retro_activity(user_id, name, start, end, photos)
            repo.clear_pending_media(user_id)
            repo.update_user_state(user_id, state_context=None)
            await message.answer(f"✅ Historically logged: **{name}** ({start.strftime('%H:%M')} - {end.strftime('%H:%M')})")
            return

        repo.complete_activity_with_media(user_id, text)
        await message.answer(f"✅ Activity logged with visual evidence: **{text}**")
        return

    # --- State Machine: WAITING_FOR_CORRECTION_SELECTION ---
    if state.get("state_context") == "WAITING_FOR_CORRECTION_SELECTION":
        try:
            choice = int(text.strip()) - 1
            options = state.get("correction_options", [])
            if 0 <= choice < len(options):
                target = options[choice]
                new_info = state.get("correction_new_info")
                res = repo.update_activity(target["id"], name=new_info.get("name"))
                
                if res["status"] == "success":
                    await message.answer(fmt.format_correction_diff(res["old"], res["new"]), parse_mode="Markdown")
                else:
                    await message.answer(fmt.format_error("Conflict detected! Integrity preserved."))
                
                repo.update_user_state(user_id, state_context=None, correction_options=None, correction_new_info=None)
            else:
                await message.answer("Invalid choice. Please send the number or /cancel.")
        except ValueError:
            await message.answer("Please send a number.")
        return

    # --- State Machine: WAITING_FOR_RESET_CODE ---
    if state.get("state_context") == "WAITING_FOR_RESET_CODE":
        expected_code = state.get("reset_code")
        if text.strip() == str(expected_code):
            repo.clear_all_user_data(user_id)
            repo.update_user_state(user_id, state_context=None, reset_code=None)
            await message.answer(fmt.format_success("DATABASE WIPED. You are now a ghost. 👻 Start fresh with /help."))
        else:
            repo.update_user_state(user_id, state_context=None, reset_code=None)
            await message.answer(fmt.format_error("Reset cancelled. Integrity maintained."))
        return

    # --- Null Safety (The Golden Rule) ---
    parsed = parser.parse(text)
    if not parsed:
        await message.answer(logic.format_unknown())
        return

    intent = parsed.get("intent")
    response = ""
    
    if intent == "start_activity":
        active_id = repo.get_active_activity(user_id)
        if active_id: repo.stop_activity(active_id)
        repo.start_activity(user_id, parsed.get("name"))
        response = fmt.format_success(logic.format_start_message(parsed.get("name")))

    elif intent == "stop_activity":
        active_id = repo.get_active_activity(user_id)
        if not active_id:
            response = fmt.format_error("You're not tracking anything right now.")
        else:
            duration = repo.stop_activity(active_id)
            repo.update_user_state(user_id, current_activity_id=None)
            response = fmt.format_success(logic.format_stop_message(duration))

    elif intent == "switch_activity":
        active_id = repo.get_active_activity(user_id)
        duration = None
        if active_id: duration = repo.stop_activity(active_id)
        repo.start_activity(user_id, parsed.get("name"))
        response = fmt.format_success(logic.format_switch_message(duration, parsed.get("name")))

    elif intent == "add_person":
        repo.add_person(user_id, parsed.get("name"), parsed.get("relationship"))
        response = fmt.format_success(logic.format_person_added(parsed.get("name"), parsed.get("relationship")))

    elif intent == "log_spending":
        repo.log_spending(user_id, parsed.get("amount"), parsed.get("category"))
        response = fmt.format_success(logic.format_spending_logged(parsed.get("amount"), parsed.get("category")))

    elif intent == "check_activity":
        active_id = repo.get_active_activity(user_id)
        if active_id:
            name = repo.get_activity_name(active_id)
            response = fmt.format_info(logic.format_check_message(name))
        else:
            response = fmt.format_error("You're not tracking anything right now.")

    elif intent == "retro_log":
        start, end, name = parsed.get("start"), parsed.get("end"), parsed.get("name")
        conflicts = repo.check_for_conflicts(user_id, start, end)
        if conflicts:
            response = fmt.format_error(f"**Conflict:** You already logged `{conflicts[0]}` during that window.")
        else:
            repo.log_retro_activity(user_id, name, start, end)
            response = fmt.format_success(f"Historically logged: **{name}** ({start.strftime('%H:%M')} to {end.strftime('%H:%M')})")

    elif intent == "retro_log_start_only":
        start, name = parsed.get("start"), parsed.get("name")
        # For start-only, we'll ask for duration or default to 1h
        # But for MVP, let's log as 1 hour and tell the user
        end = start + timedelta(hours=1)
        conflicts = repo.check_for_conflicts(user_id, start, end)
        if conflicts:
            response = fmt.format_error(f"**Conflict:** `{conflicts[0]}` is already in that time slot.")
        else:
            repo.log_retro_activity(user_id, name, start, end)
            response = fmt.format_success(f"Historically logged: **{name}** at {start.strftime('%H:%M')} (assumed 1 hour).")

    elif intent == "correction":
        import dateparser
        time_str = parsed.get("time_str")
        dt = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'past'})
        
        if not dt:
            response = fmt.format_error(f"I couldn't understand the time: `{time_str}`")
        else:
            matches = repo.find_activities_at_time(user_id, dt.isoformat())
            if not matches:
                response = fmt.format_error(f"Nothing found at {dt.strftime('%H:%M %b %d')}.")
            elif len(matches) == 1:
                # Surgical Update (Singleton)
                res = repo.update_activity(matches[0]["id"], name=parsed.get("new_name"))
                if res["status"] == "success":
                    response = fmt.format_correction_diff(res["old"], res["new"])
                else:
                    response = fmt.format_error("Conflict! The corrected time overlaps with existing logs.")
            else:
                # Surgical Selection (Ambiguity Resolution)
                repo.update_user_state(
                    user_id, 
                    state_context="WAITING_FOR_CORRECTION_SELECTION", 
                    correction_options=matches,
                    correction_new_info={"name": parsed.get("new_name")}
                )
                response = fmt.format_selection_menu(matches, dt.strftime("%H:%M"))

    elif intent == "summary":
        report = analytics.get_summary(user_id, period=parsed.get("period"))
        response = fmt.format_summary(report)

    elif intent == "reset_request":
        code = random.randint(1000, 9999)
        repo.update_user_state(user_id, state_context="WAITING_FOR_RESET_CODE", reset_code=code)
        response = fmt.format_error(f"**NUCLEAR RESET INITIATED**\n\nThis will delete ALL your logs and data. To confirm, send this code: `{code}`")

    elif intent == "tell_time":
        now = datetime.now()
        response = f"🕒 The current time is **{now.strftime('%H:%M:%S')}** (UTC+1)."

    elif intent == "set_reminder":
        repo.set_reminder(user_id, parsed.get("text"), parsed.get("time"))
        response = logic.format_reminder_set(parsed.get("text"), parsed.get("friendly_time") or parsed.get("time"))
    else:
        response = logic.format_unknown()

    await message.answer(response)
