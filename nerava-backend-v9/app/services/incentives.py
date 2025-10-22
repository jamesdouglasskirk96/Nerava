from datetime import datetime, time
from typing import List, Dict

def _parse_t(s: str) -> time:
    hh, mm, *rest = s.split(":")
    return time(int(hh), int(mm or 0))

def is_off_peak(now: datetime, window: List[str]) -> bool:
    start = _parse_t(window[0])
    end   = _parse_t(window[1])
    t = now.time()
    # Handles windows crossing midnight (e.g., 22:00–06:00)
    return (t >= start) or (t < end) if start > end else (start <= t < end)

def calc_award_cents(now: datetime, rules: List[Dict]) -> int:
    total = 0
    for r in rules:
        if not r.get("active", True):
            continue
        if r.get("code") == "OFF_PEAK_BASE":
            win = r.get("params", {}).get("window", ["22:00","06:00"])
            cents = int(r.get("params", {}).get("cents", 25))
            if is_off_peak(now, win):
                total += cents
    return total
