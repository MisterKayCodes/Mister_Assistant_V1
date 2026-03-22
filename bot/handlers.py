from aiogram import Router, types, F
from aiogram.filters import Command
from config import DB_PATH
from data.repository import Repository
from services.media_manager import MediaManager
from utils.formatter import Formatter
from bot.engine import ResponseEngine

router = Router()
repo = Repository()
manager = MediaManager()
fmt = Formatter()
engine = ResponseEngine(DB_PATH)

@router.message(Command("help"))
async def help_handler(message: types.Message):
    await message.answer(fmt.get_help_text(), parse_mode="Markdown")

@router.message(Command("summary"))
async def summary_command_handler(message: types.Message):
    user_id = str(message.from_user.id)
    await engine.handle_intent_directly(message, user_id, {"intent": "summary", "period": "today"})

@router.message(Command("start"))
async def start_handler(message: types.Message):
    user_id = str(message.from_user.id)
    repo.clear_pending_media(user_id)
    repo.update_user_state(user_id, state_context=None)
    await message.answer(fmt.format_success("MISTER ASSISTANT: PHASE 5 MODULAR! 🦾"), parse_mode="Markdown")

@router.message(F.photo)
async def photo_handler(message: types.Message):
    user_id = str(message.from_user.id)
    state = repo.get_user_state(user_id)
    path = await manager.save_photo(message.bot, message.photo[-1], user_id)
    repo.add_pending_media(user_id, path)
    
    if state.get("state_context") == "WAITING_FOR_CAPTION":
        try: await message.react([types.ReactionTypeEmoji(emoji="📥")])
        except: pass 
    else:
        repo.update_user_state(user_id, state_context="WAITING_FOR_CAPTION")
        await message.reply("📸 I've saved the photo! What activity is this for?")

@router.message()
async def telegram_handler(message: types.Message):
    await engine.handle_message(message)
