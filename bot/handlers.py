from aiogram import Router, types
from core.parser import Parser
from core.logic import Logic
from data.repository import Repository

router = Router()
parser = Parser()
logic = Logic()
repo = Repository()

@router.message()
async def telegram_handler(message: types.Message):
    user_id = str(message.from_user.id)
    text = message.text
    
    if not text:
        return

    # Core flow: Parse -> Orchestrate DB -> Logic for Response formatting
    parsed = parser.parse(text)
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
    else:
        response = logic.format_unknown()

    await message.answer(response)
