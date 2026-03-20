# 🤖 Mister Assistant - Phase 1

**Mister Assistant** is a natural conversation life tracker designed to "just work". No complexity, no over-engineering. It tracks your activities, people, spending, and reminders through natural language.

---

## 🏛️ Architecture (Flat Modular)

The project follows a flat, modular structure for maximum clarity:

- **`bot/`**: Interaction layer (Telegram handlers, CLI).
- **`core/`**: Pure logic and AI-fallback parsing.
- **`data/`**: Database persistence (SQLite).
- **`services/`**: External API integrations (Gemini/DeepSeek).
- **`utils/`**: Shared helpers and logging.
- **`docs/`**: Project roadmap and session tracking.
- **`scripts/`**: Maintenance and automation tools.
- **`Mister_Starter_Pack/`**: Templates and prompts for new project generation.

---

## 📜 The Project Rulebook (`docs/rulebook.md`)

Mister Assistant is governed by a strict **18-Rule Architectural DNA** to prevent spaghetti code and ensure long-term stability:

1. **Anatomy Control**: `core/` (Brain) must NEVER touch `aiogram` or SQL.
2. **Durable State**: No temporary RAM variables for critical state.
3. **The Escape Hatch**: Any command starting with `/` clears pending states.
4. **Boring is Good**: Readability over cleverness.

See the full [rulebook.md](file:///c:/Kaycris/Mister_Assistant_V2/docs/rulebook.md) for details.

---

## 🚀 Phase 1 Features

### ⏱️ Activity Tracking
- Natural start/stop: "starting coding", "done".
- Automatic context switching: "now lunch".
- Duration summaries.

### 🧠 People Memory
- Building a social graph through chat.
- Remembering facts and relationships.
- Contextual linking ("her birthday...").

### 💸 Spending Tracking
- Quick logging: "spent 4500 on food".
- Default payment method (PalmPay).
- Category-based totals.

### 🔔 Smart Reminders
- Natural date parsing ("tomorrow", "next Tuesday").
- Reliable triggers.

---

## 🛠️ Getting Started

1. **Setup**: Run `setup.bat` to create a virtual environment and install dependencies.
2. **Configure**: Copy `.env.example` to `.env` and add your API keys.
3. **Launch**: Run `run.bat` to start the bot with hot-reload and architecture inspection.

---

## 🛡️ "It Just Works" Guarantees

1. **Never crashes**: Graceful fallback to rule-based parsing if AI fails.
2. **Never shows errors**: Friendly clarifying questions instead of technical logs.
3. **Never loses data**: Persistent SQLite storage for everything.
