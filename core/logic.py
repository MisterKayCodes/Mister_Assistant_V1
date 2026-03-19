from datetime import datetime

class Logic:
    def __init__(self):
        pass

    def format_start_message(self, name):
        return f"⏱️ Tracking {name}"

    def format_stop_message(self, duration_seconds):
        mins = duration_seconds // 60
        return f"✅ Stopped activity. Duration: {mins}m."

    def format_switch_message(self, prev_duration_seconds, next_name):
        res = ""
        if prev_duration_seconds is not None:
            mins = prev_duration_seconds // 60
            res = f"✅ Previous activity was {mins}m. "
        return res + f"⏱️ Now tracking {next_name}"

    def format_person_added(self, name, relationship):
        return f"🤖 Got it. {name} = {relationship}"

    def format_spending_logged(self, amount, category):
        return f"✅ Logged: ₦{amount} - {category} (PalmPay?)"

    def format_unknown(self):
        return "🤖 I'm not sure how to handle that yet."
