import re
import dateparser
from datetime import datetime, timedelta

class TemporalParser:
    """Complex Natural Language time and retro-journaling logic."""
    @staticmethod
    def parse(text):
        text = text.strip()
        
        # New Pattern: "[Time] i was [Activity]" (Senior UX)
        time_first_match = re.match(r"(?i)(?P<time>.+?) (?:i was|i did) (?P<act>.+)", text)
        if time_first_match:
            time_str = time_first_match.group("time").strip()
            activity = time_first_match.group("act").strip()
            dt = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'past'})
            if dt:
                return {"intent": "retro_log_start_only", "name": activity, "start": dt}

        # Duration-based: "Yesterday I spent 3h on coding"
        duration_match = re.search(r"(?i)(?P<hours>\d+)(?:\s*h| hours?)(?: on| for)? (?P<act>.+)", text)
        if duration_match and "yesterday" in text.lower():
            hours = int(duration_match.group("hours"))
            activity = duration_match.group("act").replace("yesterday", "").strip()
            end_dt = dateparser.parse("yesterday 11pm", settings={'PREFER_DATES_FROM': 'past'})
            start_dt = end_dt - timedelta(hours=hours)
            return {"intent": "retro_log", "name": activity, "start": start_dt, "end": end_dt}

        # Flex-Journal: "Yesterday I was coding at 3pm"
        journal_match = re.search(r"(?i)(?:journal|yesterday|i did|i was) (?P<act>.+?) (?:for|on|at|yesterday.+at) (?P<time>.+)", text)
        if not journal_match:
             journal_match = re.search(r"(?i)yesterday (?P<act>.+?) at (?P<time>.+)", text)
        
        if journal_match:
            activity = journal_match.group("act").strip()
            activity = re.sub(r"(?i)^(?:i was |i did |i spent |journaling |journal |spending )", "", activity).strip()
            
            time_str = journal_match.group("time").strip()
            time_str = re.sub(r"(?i)^at ", "", time_str).strip()
            
            if "yesterday" in text.lower() and "yesterday" not in time_str.lower():
                time_str = f"yesterday {time_str}"
            
            dt = dateparser.parse(time_str, settings={'PREFER_DATES_FROM': 'past'})
            if dt:
                return {"intent": "retro_log_start_only", "name": activity, "start": dt}
        
        return None
