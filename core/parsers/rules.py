import re

class RuleParser:
    """Standard regex-based intent rules."""
    @staticmethod
    def parse(text):
        text = text.strip()
        
        # Activity Tracking
        if text.lower().startswith("starting "):
            return {"intent": "start_activity", "name": text[9:].strip()}
        if text.lower() in ["done", "stop"]:
            return {"intent": "stop_activity"}
        if text.lower().startswith("now "):
            return {"intent": "switch_activity", "name": text[4:].strip()}
        if text.lower() == "what am i doing?":
            return {"intent": "check_activity"}

        # People & Social
        person_match = re.match(r"(?i)(?:my )?(?P<rel>\w+) is (?P<name>\w+)", text)
        if person_match:
            return {"intent": "add_person", "relationship": person_match.group("rel"), "name": person_match.group("name")}
            
        # Spending
        spent_match = re.search(r"(?i)(?:spent|paid) (?P<amount>\d+) (?:on|for) (?P<category>.+)", text)
        if spent_match:
            return {"intent": "log_spending", "amount": float(spent_match.group("amount")), "category": spent_match.group("category").strip()}

        # Reminders
        remind_match = re.search(r"(?i)remind me to (?P<task>.+?) (?P<time>tomorrow|next week|at \d+:\d+|in \d+ minutes?)", text)
        if remind_match:
            return {"intent": "set_reminder", "task": remind_match.group("task"), "time": remind_match.group("time")}

        # Analytics
        if "summary" in text.lower():
            period = "today"
            if "yesterday" in text.lower(): period = "yesterday"
            elif "last week" in text.lower(): period = "last_week"
            elif "this week" in text.lower() or "weekly" in text.lower(): period = "this_week"
            elif "month" in text.lower(): period = "month"
            return {"intent": "summary", "period": period}

        return None
