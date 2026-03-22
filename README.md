# Mister Assistant

This is a personal life tracker bot for Telegram. It handles activities, spending, people facts, and reminders through natural chat. The goal is to keep things simple—no rigid commands, just talk to it.

### Core Features
- Activity tracking: Start, stop, or switch tasks naturally.
- Time machine: Log things you did yesterday or earlier today.
- Money tracking: Quick logs for spending and categories.
- Memory: Remembers facts about people you mention.
- Learning: You can teach the bot new phrases if it doesn't understand something.

### Architecture
The code follows a modular structure where every file is kept under 200 lines to maintain sanity.
- bot/: Telegram handlers and engine.
- core/: Logical parsers and processing.
- data/: SQLite storage and mixins.
- utils/: Helper functions and formatting.

### Setup and Deployment
1. Virtual Env: Run setup.bat or create your own venv and pip install -r requirements.txt.
2. Configuration: Copy .env.example to .env and fill in your keys (Gemini/DeepSeek/Telegram).
3. Run: Use run.bat for local development or python main.py for production.

The database is SQLite (mister_assistant.db) and is automatically ignored by git. Make sure to back it up if you care about your data.
