import re

class PatternCache:
    """Singleton cache for user-taught patterns. O(1) lookup."""
    _instance = None
    _patterns = {} # user_id -> list of regex_objects

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PatternCache, cls).__new__(cls)
        return cls._instance

    def load(self, user_id, pattern_list):
        """Compiles patterns into regex objects for fast matching."""
        compiled = []
        for p in pattern_list:
            try:
                regex_str = p['phrase'] if p['is_template'] else re.escape(p['phrase'])
                compiled.append({
                    "regex": re.compile(f"(?i)^{regex_str}$"),
                    "intent": p['intent'],
                    "raw": p['phrase']
                })
            except: pass
        self._patterns[user_id] = compiled

    def match(self, user_id, text):
        for p in self._patterns.get(user_id, []):
            m = p["regex"].match(text)
            if m:
                res = {"intent": p["intent"]}
                res.update(m.groupdict())
                return res
        return None
