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
        text = text.strip()
        
        # Activity Tracking
        if text.lower().startswith("starting "):
            return {"intent": "start_activity", "name": text[9:].strip()}
        if text.lower() == "done" or text.lower() == "stop":
            return {"intent": "stop_activity"}
        if text.lower().startswith("now "):
            return {"intent": "switch_activity", "name": text[4:].strip()}
        if text.lower() == "what am i doing?":
            return {"intent": "check_activity"}
        if "yesterday" in text.lower() and "do" in text.lower():
            return {"intent": "history_activity", "target": "yesterday"}

        # People Memory
        person_match = re.match(r"(?i)(?:my )?(?P<rel>\w+) is (?P<name>\w+)", text)
        if person_match:
            return {"intent": "add_person", "relationship": person_match.group("rel"), "name": person_match.group("name")}
            
        # Spending Tracking (spent or paid)
        spent_match = re.search(r"(?i)(?:spent|paid) (?P<amount>\d+) (?:on|for) (?P<category>.+)", text)
        if spent_match:
            return {
                "intent": "log_spending", 
                "amount": float(spent_match.group("amount")), 
                "category": spent_match.group("category").strip()
            }

# Reminders (Natural & Relative)
        remind_match = re.search(r"(?i)remind me to (?P<task>.+?) (?P<time>tomorrow|next week|at \d+:\d+|in \d+ minutes?)", text)
        if remind_match:
            return {"intent": "set_reminder", "task": remind_match.group("task"), "time": remind_match.group("time")}

        # Analytics (The Chronicler)
        if "summary" in text.lower():
            period = "today"
            if "yesterday" in text.lower(): period = "yesterday"
            elif "last week" in text.lower(): period = "last_week"
            elif "this week" in text.lower() or "weekly" in text.lower(): period = "this_week"
            elif "month" in text.lower(): period = "month"
            return {"intent": "summary", "period": period}

        if "delete all" in text.lower() and "data" in text.lower():
            return {"intent": "reset_request"}
            
        return None
            
            # Simple Relative & Natural Resolver
            from datetime import datetime, timedelta
            now = datetime.now()
            
            if "in" in time_raw and "minute" in time_raw:
                try:
                    mins = int(re.search(r"\d+", time_raw).group())
                    future = now + timedelta(minutes=mins)
                    iso_time = future.strftime("%Y-%m-%d %H:%M:%S")
                    friendly_time = future.strftime("%H:%M today")
                except: pass
            elif "tomorrow" in time_raw:
                iso_time = (now + timedelta(days=1)).strftime("%Y-%m-%d 09:00:00")
                friendly_time = "09:00 tomorrow"
            elif "at" in time_raw:
                # e.g. "at 18:00"
                t_match = re.search(r"(\d+):(\d+)", time_raw)
                if t_match:
                    h, m = t_match.groups()
                    iso_time = now.replace(hour=int(h), minute=int(m), second=0).strftime("%Y-%m-%d %H:%M:%S")
                    friendly_time = f"{h}:{m} today"

            return {"intent": "set_reminder", "text": task, "time": iso_time, "friendly_time": friendly_time}

        # --- RETRO-LOGGING SENSING (Rule 11) ---
        import dateparser
        # Patterns like: "I watched a movie from 2pm to 4pm" or "watched movie at 2pm"
        retro_match = re.match(r"(?i)(?:i )?(?P<act>.+?) (?:at|from) (?P<time>.+)", text)
        if retro_match:
            activity = retro_match.group("act")
            time_str = retro_match.group("time")
            
            # Handle "from X to Y" explicitly
            if " to " in time_str:
                parts = time_str.split(" to ")
                start_dt = dateparser.parse(parts[0], settings={'PREFER_DATES_FROM': 'past'})
                end_dt = dateparser.parse(parts[1], settings={'PREFER_DATES_FROM': 'past'})
                if start_dt and end_dt:
                    return {"intent": "retro_log", "name": activity, "start": start_dt, "end": end_dt}
            
            # Handle "at X"
            dt = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'past'})
            if dt:
                # Default to 1-hour session ending at that time (or starting?)
                # Senior Decision: "at X" usually means the START of the session.
                return {"intent": "retro_log_start_only", "name": activity, "start": dt}

        # --- UTILITY INTENTS ---
        if any(x in text for x in ["what time", "current time", "the time"]):
            return {"intent": "tell_time"}

        return None

    def ai_parse(self, text):
        # Placeholder for Gemini/DeepSeek integration
        return {"intent": "unknown", "text": text}
