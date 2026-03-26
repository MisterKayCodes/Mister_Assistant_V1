from datetime import datetime

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

    def get_help_text(self):
        return (
            "🌟 **Mister Assistant: Full Command Manual** 🌟\n\n"
            "I help you track your life, money, and tasks. Here is my full capability:\n\n"
            "🕒 **1. ACTIVITY TRACKING (Real-time)**\n"
            "• `Starting [Activity]` - Start a clock.\n"
            "• `Done` or `Stop` - Stop the clock.\n"
            "• `Switch to [Activity]` - Stop current and start new.\n"
            "• `/summary` - See today's breakdown.\n\n"
            "🕰️ **2. THE TIME MACHINE (Retro-Logging)**\n"
            "• `Yesterday I was [Activity] at 3pm` - Log at exact time.\n"
            "• `Yesterday I spent 2h on [Activity]` - Log a duration.\n"
            "• `I was at [Activity] from 10am to 12pm` - Log a range.\n\n"
            "✏️ **3. CORRECTIONS & DELETIONS**\n"
            "• `Fix 6am` - Correct the activity at a specific time.\n"
            "• `Delete [Activity Name]` - Remove a specific entry.\n"
            "• `Actually I was [Activity]` - Fix your CURRENT session.\n\n"
            "💰 **4. MONEY & PEOPLE**\n"
            "• `Spent 50 on [Category]` - Log expenses.\n"
            "• `Note: [Name] is [Relationship]` - Save facts about people.\n"
            "• `Reminder: [Text] at [Time]` - Set future alerts.\n\n"
            "🚀 **5. TASK SCHEDULER (Deep Focus)**\n"
            "• `Tasks: [List] | Duration: [Time]` - Start a timed session.\n"
            "• `/status` - Visual progress bar + checklist.\n"
            "• `/history` - View past productivity logs.\n\n"
            "🎓 **6. TEACHING ME**\n"
            "• If I don't understand, just follow the **Teaching Menu**.\n"
            "• `/cancel` - Stop any active process."
        )

    def format_summary(self, summary_data):
        period = summary_data["period"].replace("_", " ").upper()
        data = summary_data["data"]
        total_seconds = summary_data["total_seconds"]
        
        if not data:
            return self.format_info(
                f"**SUMMARY: {period}**\n━━━━━━━━━━━━━━━━━━\n"
                "Your timeline is a blank canvas today! 🎨\n"
                "Start your first activity with 'Gym' or 'Working'."
            )

        # Category Map (CTO Directive)
        cat_map = {
            "Work": ["Work", "Coding", "Project", "Deep work", "Office"],
            "Health": ["Gym", "Workout", "Run", "Yoga", "Exercise", "Nap"],
            "Food": ["Lunch", "Dinner", "Breakfast", "Snack", "Eating"],
            "Sleep": ["Sleep", "Sleeping"]
        }
        
        # Aggregate by categories
        cat_totals = {} # Label -> seconds
        for activity, seconds in data.items():
            found = False
            for cat, keywords in cat_map.items():
                if any(kw.lower() in activity.lower() for kw in keywords):
                    emoji = {"Work": "💻", "Health": "🧘", "Food": "🍱", "Sleep": "💤"}[cat]
                    label = f"{emoji} **{cat}**"
                    cat_totals[label] = cat_totals.get(label, 0) + seconds
                    found = True
                    break
            if not found:
                label = f"🎯 **Other**"
                cat_totals[label] = cat_totals.get(label, 0) + seconds

        # Build UI string
        res = f"📊 **SUMMARY: {period}**\n━━━━━━━━━━━━━━━━━━\n"
        
        # Sort by duration
        sorted_cats = sorted(cat_totals.items(), key=lambda x: x[1], reverse=True)
        
        for label, seconds in sorted_cats:
            h = seconds // 3600
            m = (seconds % 3600) // 60
            percent = (seconds / total_seconds) * 100 if total_seconds > 0 else 0
            
            # Progress bar (10 segments)
            filled = int(percent / 10)
            bar = "▰" * filled + "▱" * (10 - filled)
            
            res += f"{label}: `{h}h {m}m` [{bar}] `{int(percent)}%`\n"

        res += "━━━━━━━━━━━━━━━━━━\n"
        total_h = total_seconds // 3600
        total_m = (total_seconds % 3600) // 60
        res += f"🏁 **Total Logged:** `{total_h}h {total_m}m`"
        
        return res

    def format_correction_diff(self, old_data, new_data):
        """High-Diff UI Rule 11: Show the Delta."""
        _, old_name, old_start_str, old_end_str = old_data
        _, new_name, new_start_str, new_end_str = new_data
        
        old_start = datetime.fromisoformat(old_start_str)
        old_end = datetime.fromisoformat(old_end_str) if old_end_str else datetime.now()
        new_start = datetime.fromisoformat(new_start_str)
        new_end = datetime.fromisoformat(new_end_str) if new_end_str else datetime.now()
        
        old_dur = (old_end - old_start).total_seconds()
        new_dur = (new_end - new_start).total_seconds()
        delta_mins = int((new_dur - old_dur) // 60)
        delta_str = f"{delta_mins}m" if delta_mins < 0 else f"+{delta_mins}m"

        return (
            "✏️ **LOG UPDATED!**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"❌ **From:** {old_name} ({old_start.strftime('%H:%M')} - {old_end.strftime('%H:%M')})\n"
            f"✅ **To:** {new_name} ({new_start.strftime('%H:%M')} - {new_end.strftime('%H:%M')})\n\n"
            f"⏱️ **Change:** `{delta_str}`\n"
            f"📅 **Date:** {new_start.strftime('%b %d')}\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Your summary has been adjusted!"
        )

    def format_learning_menu(self, phrase):
        return (
            "🎓 **UNIVERSAL TEACHING MENU**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Phrase: `{phrase}`\n\n"
            "**TRACKING**\n"
            "1. Start Activity  2. Stop Activity  3. Switch\n"
            "4. Retro-Log (Range)  5. Retro-Log (Start)\n\n"
            "**TASKS**\n"
            "6. Start Task Session  7. Task Status\n\n"
            "**SOCIAL & MONEY**\n"
            "8. Log Spending  9. Add Person  10. Set Reminder\n\n"
            "**SYSTEM**\n"
            "11. Get Summary  12. Tell Current Time\n\n"
            "13. **Ignore**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            "Reply with **number** to link or /cancel."
        )

    def format_footer(self, context=None):
        if not context: return "\n\n`🤖 Status: Listening...`"
        modes = {
            "WAITING_FOR_CAPTION": "Waiting for Photo Caption 🖼️",
            "WAITING_FOR_CORRECTION_SELECTION": "Waiting for Selection 🧐",
            "WAITING_FOR_DELETION_SELECTION": "Waiting for Deletion Choice ⚠️",
            "WAITING_FOR_LEARNING_INTENT": "Learning New Phrase... 🎓",
            "WAITING_FOR_GENERALIZATION": "Refining Pattern Logic 🧬",
            "WAITING_FOR_RESET_CODE": "Nuclear Authorization Required ☢️",
            "WAITING_FOR_TASK_LOG": "Documenting Your Success 🦾",
        }
        mode = modes.get(context, "Ready")
        return f"\n\n`🤖 Mode: {mode}`"

    def format_generalization_request(self, phrase):
        return (
            "🧬 **GENERALIZATION CHECK**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"Phrase: `{phrase}`\n\n"
            "Is there a **variable** part (like an activity name) in this phrase?\n\n"
            "• If yes, **type the word** I should generalize (e.g. if the phrase is 'Deep in Gym', type `Gym`).\n"
            "• If no, type **'Fixed'**.\n"
            "━━━━━━━━━━━━━━━━━━"
        )
