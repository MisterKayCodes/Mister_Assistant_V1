import os
from dotenv import load_dotenv

load_dotenv()

# API Configuration
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY")

# Bot Configuration
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
USE_AI = os.getenv("USE_AI", "True").lower() == "true"
API_CALLS_DAILY_LIMIT = 900

# Database Configuration
DB_PATH = os.path.join(os.path.dirname(__file__), "data", "mister_assistant.db")

# Logic Configuration
MAX_ACTIVITY_DURATION_HOURS = 8
DEFAULT_REMINDER_TIME = "09:00"

# Logging Configuration
LOG_FILE = os.path.join(os.path.dirname(__file__), "logs", "mister_assistant.log")
