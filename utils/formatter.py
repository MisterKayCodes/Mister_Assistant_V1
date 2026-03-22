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

    def format_help(self):
        return (
            "📚 **MISTER ASSISTANT: LIFE OS MANUAL**\n\n"
            "📈 **ACTIVITY DOCUMENTATION**\n"
            "• `starting coding` - Start a timer.\n"
            "• `now gym` - Stop current and start new.\n"
            "• `done` or `stop` - Finish tracking.\n"
            "• `what am i doing?` - Check status.\n\n"
            "📊 **ANALYTICS (Phase 4)**\n"
            "• `/summary` - Today's report.\n"
            "• `yesterday summary` - Past report.\n"
            "• `last week summary` - Weekly report.\n\n"
            "🕰️ **THE TIME MACHINE**\n"
            "• `watched movie from 2pm to 4pm`\n"
            "• `gym at 6am` (Assumes 1hr session)\n"
            "• **Photo Retro**: Send Photo then caption: `Lunch at 1pm`.\n"
            "• 🚩 Conflict Guard will block overlapping logs!\n\n"
            "📸 **VISUAL EVIDENCE**\n"
            "• Send a photo to start a 'Visual Session'.\n"
            "• Caption later to link all pending photos.\n\n"
            "💰 **FINANCE & SOCIAL**\n"
            "• `spent 5000 on lunch` - Log expense.\n"
            "• `My sister is Chichi` - Person memory.\n\n"
            "🤖 **UTILITIES**\n"
            "• `what time is it?` - Accurate time check.\n"
            "• `/help` - Open this manual.\n"
            "• `/reset_all_data` - Delete all my data.\n\n"
            "🦾 *High Performance. Durable Memory. Accurate Timeline.*"
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
