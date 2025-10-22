# app/services/cache.py
import time
from typing import Any, Dict, Tuple

class TTLCache:
    def __init__(self):
        self._store: Dict[str, Tuple[float, Any]] = {}

    def get(self, key: str):
        item = self._store.get(key)
        if not item:
            return None
        exp, val = item
        if exp < time.time():
            self._store.pop(key, None)
            return None
        return val

    def set(self, key: str, value: Any, ttl_seconds: int):
        self._store[key] = (time.time() + ttl_seconds, value)

cache = TTLCache()

# Simple click-session journal to reconcile webhooks to clicks
class ClickStore:
    def __init__(self):
        self._events = []  # [{user_id, hub_id, merchant, ts, link}]
    def record(self, user_id: str, hub_id: str, merchant: str, link: str):
        self._events.append({
            "user_id": user_id, "hub_id": hub_id,
            "merchant": merchant, "link": link, "ts": time.time()
        })
    def last_for(self, user_id: str, merchant: str, hours: int = 6):
        cutoff = time.time() - hours * 3600
        for e in reversed(self._events):
            if e["ts"] >= cutoff and e["user_id"] == user_id and e["merchant"] == merchant:
                return e
        return None

clicks = ClickStore()
