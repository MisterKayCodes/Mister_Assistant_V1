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
            "🌟 **Mister Assistant: Your Self-Evolving Helper** 🌟\n\n"
            "Hey! I'm here to help you track your life. I'm getting smarter every day! Here is how you talk to me:\n\n"
            "🕒 **1. LOGGING TIME (Right Now)**\n"
            "• `Starting Gym` - I'll start a timer for Gym.\n"
            "• `Done Gym` or `Stop` - I'll stop the timer.\n"
            "• `Switch to Lunch` - Stops Gym and starts Lunch instantly.\n\n"
            "🕰️ **2. THE TIME MACHINE (Past Logs)**\n"
            "• `Yesterday I was Coding at 3pm` - I'll log it at that exact time.\n"
            "• `Yesterday I spent 2h on Housework` - I'll log a 2-hour block.\n"
            "• `I was at the Gym from 10am to 12pm` - I'll log the full range.\n\n"
            "💰 **3. TRACKING MONEY**\n"
            "• `Spent 50 on Pizza` - I'll log a $50 expense.\n"
            "• `Pizza cost 10` - Another way to log spending.\n\n"
            "✏️ **4. FIXING MISTAKES**\n"
            "• `Actually I was Gaming` - Changes your current activity.\n"
            "• `Fix 6am` - I'll find what you did at 6am and let you change it!\n"
            "• `Delete Hi` - I'll find 'Hi' and remove it forever.\n\n"
            "🎓 **5. TEACHING ME (New!)**\n"
            "• If you say something I don't know, I will ask you to **Teach** me.\n"
            "• You can link your words to my features (like 'Start Activity').\n"
            "• You can use **/cancel** any time to stop learning.\n\n"
            "📊 **6. SUMMARIES & DATA**\n"
            "• `/summary` - See everything you did today.\n"
            "• `/reset_all_data` - Wipes my memory (needs a secret code!).\n"
            "• `/cancel` - Stops whatever we are doing right now.\n\n"
            "💡 **Remember:** Watch my `🤖 Status` at the bottom of my messages to see if I'm listening or learning!"
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
            "🎓 **I'M LEARNING...**\n"
            "━━━━━━━━━━━━━━━━━━\n"
            f"❓ **Unknown Phrase:** `{phrase}`\n\n"
            "How should I handle this in the future?\n"
            "1. **Start Activity** (e.g. 'Starting...')\n"
            "2. **Stop Activity** (e.g. 'Done')\n"
            "3. **Switch Activity** (e.g. 'Now...')\n"
            "4. **Get Summary**\n"
            "5. **Log Spending**\n"
            "6. **Ignore**\n"
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
