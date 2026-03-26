# UI elements for Telegram
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

def get_task_warning_keyboard(task_id):
    """Senior Refinement #1: Inline Buttons for accountability."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ All Done", callback_data=f"task_done:{task_id}"),
            InlineKeyboardButton(text="⏳ Snooze (15m)", callback_data=f"task_snooze:{task_id}")
        ],
        [
            InlineKeyboardButton(text="❌ Cancel Task", callback_data=f"task_cancel:{task_id}")
        ]
    ])
