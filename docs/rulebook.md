# 🧬 Mister_Assistant ARCH DNA (2025 Edition)

Every line of code in this project must adhere to the following Anatomy and Rules. If a request violates these, flag the "Mutant" and propose a fix.

## 🏛️ 1. The Anatomy (Folder Restrictions)

### `core/` (The Brain)
- **Role**: Pure logic/math/state machines.
- **Rule**: NO imports of `aiogram`, database, or external APIs.

### `services/` (The Nervous System)
- **Role**: External connections and heavy lifting.
- **Rule**: Only place for `requests`, `aiohttp`, `websockets`, or file system IO for media.

### `bot/` (The Mouth/Ears)
- **Role**: Telegram interface.
- **Rule**: NO math, NO direct SQL. Translates user input to `Core` or `Service` calls.

### `data/` (The Memory)
- **Role**: Persistence only.
- **Rule**: All DB access must go through `repository.py`.

---

## 📜 2. The 18 Golden Rules

1.  **Known State**: The system must always know its current status.
2.  **Durable Storage**: Store all critical state in DB, never just in RAM.
3.  **Single Responsibility**: One file = One job.
4.  **Explicit Logic**: No "magical" code; use readable variable names.
5.  **Idempotency**: Same input must result in the same state/result.
6.  **No Guessing**: Wait for explicit commands; never assume intent. (Escape Hatch: `/` always clears state).
7.  **Design for Failure**: Always use try/except for recovery.
8.  **Boring is Good**: Prioritize readability over clever one-liners.
9.  **Automated Testing**: Core logic must be testable.
10. **Observability**: Detailed logs with timestamps are mandatory.
11. **Separation**: Business logic must stay separate from Integrations.
12. **Explicit Errors**: Never crash silently; log the context.
13. **Pinned Dependencies**: Use specific versions for libraries.
14. **Security**: Sanitize all inputs; never log sensitive data.
15. **Clean Git**: Atomic commits with clear messages.
16. **Boy Scout Rule**: Leave code cleaner than you found it.
17. **Documentation**: Explain the "Why," not just the "How."
18. **Safe Deployment**: Backup -> Staging -> Update -> Monitor.
