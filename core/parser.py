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
            
        # Spending Tracking
        spent_match = re.search(r"spent (?P<amount>\d+) on (?P<category>\w+)", text)
        if spent_match:
            return {
                "intent": "log_spending", 
                "amount": float(spent_match.group("amount")), 
                "category": spent_match.group("category")
            }

        # Reminders
        remind_match = re.search(r"remind me to (?P<task>.+?) (?P<time>tomorrow|next week|at \d+:\d+)", text)
        if remind_match:
            return {"intent": "set_reminder", "text": remind_match.group("task"), "time": remind_match.group("time")}

        return None

    def ai_parse(self, text):
        # Placeholder for Gemini/DeepSeek integration
        # Real implementation would use Gemini API here
        return None
