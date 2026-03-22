import re

class EditParser:
    """Correction and deletion logic."""
    @staticmethod
    def parse(text):
        text = text.strip()
        
        # --- CORRECTION ENGINE ---
        c_match = re.match(r"(?i)correct (?P<old>.+?) at (?P<time>.+?) to (?P<new>.+)", text)
        if c_match:
            return {"intent": "correction", "old_name": c_match.group("old").strip(), "time_str": c_match.group("time").strip(), "new_name": c_match.group("new").strip()}
            
        a_match = re.match(r"(?i)actually i was (?P<new>.+?) at (?P<time>.+)", text)
        if a_match:
            return {"intent": "correction", "time_str": a_match.group("time").strip(), "new_name": a_match.group("new").strip()}

        f_match = re.match(r"(?i)fix (?P<time>.+?) it was (?P<new>.+)", text)
        if f_match:
            return {"intent": "correction", "time_str": f_match.group("time").strip(), "new_name": f_match.group("new").strip()}

        # --- DELETION ENGINE ---
        d_match = re.match(r"(?i)(?:delete|remove) (?P<target>.+?) at (?P<time>.+)", text)
        if d_match:
            return {"intent": "delete_activity", "name": d_match.group("target").strip(), "time_str": d_match.group("time").strip()}
        
        d_simple = re.match(r"(?i)(?:delete|remove) (?P<target>.+)", text)
        if d_simple:
             target = d_simple.group("target").strip()
             if target.lower() not in ["all", "everything"]:
                return {"intent": "delete_activity", "name": target}

        # Nuclear
        if "delete all" in text.lower() and "data" in text.lower():
            return {"intent": "reset_request"}

        return None
