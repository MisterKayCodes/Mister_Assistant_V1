from aiogram import Router, types
from aiogram.filters import Command
from core.parser import Parser
from core.logic import Logic
from data.repository import Repository

router = Router()
parser = Parser()
logic = Logic()
repo = Repository()

@router.message(Command("start"))
async def start_handler(message: types.Message):
    print(f"DEBUG: /start command received from {message.from_user.id}")
    await message.answer("🤖 **Mister Assistant Phase 1 Online!**\n\nI can track your activities, spending, and remember people. Try saying 'starting coding' or 'spent 500 on lunch'!")

@router.message()
async def telegram_handler(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text
    
    if not text:
        return

    # --- Null Safety (The Golden Rule) ---
    parsed = parser.parse(text)
    if not parsed:
        print(f"DEBUG: Parser returned None for input: {text}")
        await message.answer(logic.format_unknown())
        return

    intent = parsed.get("intent")
    
    response = ""
    
    if intent == "start_activity":
        active_id = repo.get_active_activity(user_id)
        if active_id:
            repo.stop_activity(active_id)
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
        if active_id:
            duration = repo.stop_activity(active_id)
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
    elif intent == "set_reminder":
        repo.set_reminder(user_id, parsed.get("text"), parsed.get("time"))
        response = logic.format_reminder_set(parsed.get("text"), parsed.get("time"))
    else:
        response = logic.format_unknown()

    await message.answer(response)
