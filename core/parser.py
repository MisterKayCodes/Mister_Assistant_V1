import re
from config import USE_AI, API_CALLS_DAILY_LIMIT

class Parser:
    def __init__(self):
        self.api_calls_today = 0

    def parse(self, text):
        # 1. Try Rule-based / Regex fallback first for speed/certainty
        fallback_result = self.fallback_parse(text)
        if fallback_result:
            return fallback_result

        # 2. Try AI parsing
        if USE_AI and self.api_calls_today < API_CALLS_DAILY_LIMIT:
            try:
                result = self.ai_parse(text)
                self.api_calls_today += 1
                return result
            except:
                pass # Fallback to clarification or broader rules

        return {"intent": "unknown", "text": text}

    def fallback_parse(self, text):
        text = text.lower().strip()
        
        # Activity Tracking
        if text.startswith("starting "):
            return {"intent": "start_activity", "name": text.replace("starting ", "").strip()}
        if text == "done" or text == "stop":
            return {"intent": "stop_activity"}
        if text.startswith("now "):
            return {"intent": "switch_activity", "name": text.replace("now ", "").strip()}
        if text == "what am i doing?":
            return {"intent": "check_activity"}
        if "yesterday" in text and "do" in text:
            return {"intent": "history_activity", "target": "yesterday"}

        # People Memory
        person_match = re.match(r"(?:my )?(?P<rel>\w+) is (?P<name>\w+)", text)
        if person_match:
            return {"intent": "add_person", "relationship": person_match.group("rel"), "name": person_match.group("name")}
            
        # Spending Tracking (spent or paid)
        spent_match = re.search(r"(?:spent|paid) (?P<amount>\d+) (?:on|for) (?P<category>.+)", text)
        if spent_match:
            return {
                "intent": "log_spending", 
                "amount": float(spent_match.group("amount")), 
                "category": spent_match.group("category").strip()
            }

        # Reminders (Natural & Relative)
        remind_match = re.search(r"remind me to (?P<task>.+?) (?P<time>tomorrow|next week|at \d+:\d+|in \d+ minutes?)", text)
        if remind_match:
            task = remind_match.group("task")
            time_raw = remind_match.group("time")
            
            # Simple Relative Resolver
            if "in" in time_raw and "minute" in time_raw:
                try:
                    mins = int(re.search(r"\d+", time_raw).group())
                    from datetime import datetime, timedelta
                    future = datetime.now() + timedelta(minutes=mins)
                    time_raw = future.strftime("%H:%M today")
                except:
                    pass
            
            return {"intent": "set_reminder", "text": task, "time": time_raw}

        return None

    def ai_parse(self, text):
        # Placeholder for Gemini/DeepSeek integration
        return {"intent": "unknown", "text": text}
