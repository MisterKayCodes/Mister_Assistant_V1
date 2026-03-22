from core.parsers.cache import PatternCache
from core.parsers.rules import RuleParser
from core.parsers.temporal import TemporalParser
from core.parsers.edit import EditParser
from config import USE_AI, API_CALLS_DAILY_LIMIT

class Parser:
    def __init__(self):
        self.api_calls_today = 0
        self.cache = PatternCache()

    def parse(self, text, user_id=None):
        """Main entry point for intent parsing."""
        # 1. Static Utilities (Highest Priority)
        # Rule: Core features like /time should NEVER be hijacked by learned patterns
        if any(x in text.lower() for x in ["what time", "current time", "the time"]):
            return {"intent": "tell_time"}

        # 2. Check Custom Cache (O(1))
        if user_id:
            custom_res = self.cache.match(user_id, text)
            if custom_res: return custom_res

        # 3. Sequential Rule Chains
        for sub_parser in [RuleParser, TemporalParser, EditParser]:
            res = sub_parser.parse(text)
            if res: return res

        # 4. AI Fallback (Future Phase)
        return {"intent": "unknown", "text": text}
