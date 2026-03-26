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

        # Task Management (Senior Refinement #4: Input Flexibility)
        # Pattern: Tasks: A, B, C | Duration: 4h
        task_match = re.search(r"(?i)tasks:\s*(?P<list>.+?)\s*\|\s*duration:\s*(?P<dur>.+)", text)
        if task_match:
            task_list = [t.strip() for t in task_match.group("list").split(",")]
            dur_str = task_match.group("dur").strip().lower()
            
            # Simple duration parser (Senior Refinement #4)
            minutes = 0
            match = re.search(r"(\d+)\s*(h|m|hour|min)", dur_str)
            if match:
                val = int(match.group(1))
                unit = match.group(2)
                if unit.startswith("h"): minutes = val * 60
                else: minutes = val
            elif dur_str.isdigit():
                minutes = int(dur_str)
                
            if minutes > 0:
                return {"intent": "add_tasks", "task_list": task_list, "duration_minutes": minutes}

        return None
