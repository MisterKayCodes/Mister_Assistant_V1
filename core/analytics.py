import sqlite3
from datetime import datetime, timedelta
from typing import Dict, List, Any

class AnalyticsEngine:
    def __init__(self, db_path):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def get_summary(self, user_id: str, period: str = "today") -> Dict[str, Any]:
        """Calculates activity aggregates for a period. Clips durations at boundaries (Midnight Split)."""
        now = datetime.now()
        
        # Define boundaries
        if period == "today":
            start_bound = now.replace(hour=0, minute=0, second=0, microsecond=0)
            end_bound = start_bound + timedelta(days=1)
        elif period == "yesterday":
            end_bound = now.replace(hour=0, minute=0, second=0, microsecond=0)
            start_bound = end_bound - timedelta(days=1)
        elif period == "this_week":
            start_bound = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            end_bound = start_bound + timedelta(days=7)
        elif period == "last_week":
            this_week_start = (now - timedelta(days=now.weekday())).replace(hour=0, minute=0, second=0, microsecond=0)
            start_bound = this_week_start - timedelta(days=7)
            end_bound = this_week_start
        else: # month
            start_bound = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
            end_bound = (start_bound + timedelta(days=32)).replace(day=1)

        conn = self._get_conn()
        cursor = conn.cursor()
        
        # Query: Get all tasks that overlap with the boundary
        # Normalize: name.strip().capitalize()
        cursor.execute(
            """SELECT name, start_time, end_time 
               FROM activities 
               WHERE user_id = ? 
               AND datetime(start_time) < datetime(?) 
               AND (end_time IS NULL OR datetime(end_time) > datetime(?))""",
            (user_id, end_bound, start_bound)
        )
        
        rows = cursor.fetchall()
        aggregates = {} # Name -> seconds
        
        for name, start_str, end_str in rows:
            # 1. Parse times
            start = datetime.fromisoformat(start_str)
            end = datetime.fromisoformat(end_str) if end_str else now
            
            # 2. Clip at boundaries (The Midnight Split)
            clip_start = max(start, start_bound)
            clip_end = min(end, end_bound)
            
            if clip_end <= clip_start:
                continue
                
            duration = int((clip_end - clip_start).total_seconds())
            
            # 3. Normalization (The Gym vs gym War)
            norm_name = name.strip().capitalize()
            
            aggregates[norm_name] = aggregates.get(norm_name, 0) + duration

        conn.close()
        return {
            "period": period,
            "start": start_bound,
            "end": end_bound,
            "data": aggregates,
            "total_seconds": sum(aggregates.values())
        }
