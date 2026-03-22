class Formatter:
    @staticmethod
    def format_title(text):
        return f"✨ **{text.upper()}** ✨"

    @staticmethod
    def format_activity(name, start, end=None):
        time_str = f"{start.strftime('%H:%M')}"
        if end:
            time_str += f" - {end.strftime('%H:%M')}"
        return f"⏱️ `{name}` | {time_str}"

    @staticmethod
    def format_success(text):
        return f"✅ {text}"

    @staticmethod
    def format_error(text):
        return f"⚠️ {text}"

    @staticmethod
    def format_info(text):
        return f"🤖 {text}"

    @staticmethod
    def format_help():
        return (
            "📚 **MISTER ASSISTANT: LIFE OS MANUAL**\n\n"
            "📈 **ACTIVITY DOCUMENTATION**\n"
            "• `starting coding` - Start a timer.\n"
            "• `now gym` - Stop current and start new.\n"
            "• `done` or `stop` - Finish tracking.\n"
            "• `what am i doing?` - Check status.\n\n"
            "🕰️ **THE TIME MACHINE** (Phase 3)\n"
            "• `watched movie from 2pm to 4pm`\n"
            "• `gym at 6am` (Assumes 1hr session)\n"
            "• **Photo Retro**: Send [Photo] then caption: `Lunch at 1pm`.\n"
            "• 🚩 *Conflict Guard will block overlapping logs!*\n\n"
            "📸 **VISUAL EVIDENCE** (Phase 2)\n"
            "• Send a photo to start a 'Visual Session'.\n"
            "• Caption later to link all pending photos.\n"
            "• Use `/cancel` to clear the photo queue.\n\n"
            "💰 **FINANCE & SOCIAL**\n"
            "• `spent 5000 on lunch` - Log expense.\n"
            "• `My sister is Chichi` - Remember people.\n\n"
            "🤖 **UTILITIES**\n"
            "• `what time is it?` - Accurate time check.\n"
            "• `/help` - This manual.\n\n"
            "🦾 *High Performance. Durable Memory. Accurate Timeline.*"
        )
