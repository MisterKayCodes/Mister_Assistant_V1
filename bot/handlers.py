from aiogram import Router, types, F
from aiogram.filters import Command
from core.parser import Parser
from core.logic import Logic
from data.repository import Repository
from services.media_manager import MediaManager

router = Router()
parser = Parser()
logic = Logic()
repo = Repository()
manager = MediaManager()

@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(
        "📚 **Mister Assistant Multi-Modal Manual**\n\n"
        "Here is how you can use my High-Trust Features:\n\n"
        "📈 **Activity Documentation**\n"
        "- `starting coding` - start a timer\n"
        "- `now gym` - stop old activity and start a new one\n"
        "- `what am i doing?` - check current status\n"
        "- `done` or `stop` - finish an activity\n\n"
        "📸 **Visual Evidence (Phase 2)**\n"
        "- **Send a Photo** - I'll save it and wait for a caption.\n"
        "- **Caption later** - Send text like 'Lunch' to link pending photos.\n"
        "- **Multi-Photo** - Send many at once; I'll collect them all silently.\n"
        "- `/cancel` - reset the photo memory queue.\n\n"
        "💰 **Financial & Social**\n"
        "- `spent 5000 on pizza` - log spending\n"
        "- `My sister is Chichi` - remember relationships\n\n"
        "🔔 **Tasks & Reminders**\n"
        "- `remind me to pay bills at 18:00`\n"
        "- `remind me to check oven in 10 minutes`\n\n"
        "🦾 *I am designed for High Performance and Durable Memory.*"
    )

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    # Rule 1: Known State - Reset everything on start
    repo.clear_pending_media(user_id)
    repo.update_user_state(user_id, state_context=None)
    print(f"DEBUG: /start command received from {user_id}")
    await message.answer("🤖 **Mister Assistant Phase 2 Online!**\n\nI can now see and remember. Send me a photo to log an activity with visual evidence, or use `/help` to see everything I can do!")

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

    # --- Escape Hatch (Rule 6) ---
    if text.startswith("/"):
        repo.clear_pending_media(user_id)
        repo.update_user_state(user_id, state_context=None)
        if text != "/start":
            await message.answer("🤖 Action cancelled. How can I help you?")
        return

    # --- State Machine: WAITING_FOR_CAPTION ---
    state = repo.get_user_state(user_id)
    if state.get("state_context") == "WAITING_FOR_CAPTION":
        # Rule 5: Idempotency / JSON Serialization handled in Repo
        # Senior Check: Does the caption have a retro-time?
        parsed_caption = parser.parse(f"i {text}") # Try parsing as Retro-Log
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
        response = logic.format_start_message(parsed.get("name"))

    elif intent == "stop_activity":
        active_id = repo.get_active_activity(user_id)
        if not active_id:
            response = "🤖 You're not tracking anything right now."
        else:
            duration = repo.stop_activity(active_id)
            repo.update_user_state(user_id, current_activity_id=None)
            response = logic.format_stop_message(duration)

    elif intent == "switch_activity":
        active_id = repo.get_active_activity(user_id)
        duration = None
        if active_id: duration = repo.stop_activity(active_id)
        repo.start_activity(user_id, parsed.get("name"))
        response = logic.format_switch_message(duration, parsed.get("name"))

    elif intent == "add_person":
        repo.add_person(user_id, parsed.get("name"), parsed.get("relationship"))
        response = logic.format_person_added(parsed.get("name"), parsed.get("relationship"))

    elif intent == "log_spending":
        repo.log_spending(user_id, parsed.get("amount"), parsed.get("category"))
        response = logic.format_spending_logged(parsed.get("amount"), parsed.get("category"))

    elif intent == "check_activity":
        active_id = repo.get_active_activity(user_id)
        if active_id:
            name = repo.get_activity_name(active_id)
            response = logic.format_check_message(name)
        else:
            response = "🤖 You're not tracking anything right now."

    elif intent == "retro_log":
        start, end, name = parsed.get("start"), parsed.get("end"), parsed.get("name")
        conflicts = repo.check_for_conflicts(user_id, start, end)
        if conflicts:
            response = f"⚠️ **Conflict:** You already logged `{conflicts[0]}` during that window."
        else:
            repo.log_retro_activity(user_id, name, start, end)
            response = f"✅ Historically logged: **{name}** ({start.strftime('%H:%M')} to {end.strftime('%H:%M')})"

    elif intent == "retro_log_start_only":
        start, name = parsed.get("start"), parsed.get("name")
        # For start-only, we'll ask for duration or default to 1h
        # But for MVP, let's log as 1 hour and tell the user
        end = start + timedelta(hours=1)
        conflicts = repo.check_for_conflicts(user_id, start, end)
        if conflicts:
            response = f"⚠️ **Conflict:** `{conflicts[0]}` is already in that time slot."
        else:
            repo.log_retro_activity(user_id, name, start, end)
            response = f"✅ Historically logged: **{name}** at {start.strftime('%H:%M')} (assumed 1 hour)."

    elif intent == "set_reminder":
        repo.set_reminder(user_id, parsed.get("text"), parsed.get("time"))
        response = logic.format_reminder_set(parsed.get("text"), parsed.get("friendly_time") or parsed.get("time"))
    else:
        response = logic.format_unknown()

    await message.answer(response)
