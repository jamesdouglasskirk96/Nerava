import json

def to_json(d: dict) -> str:
    """Convert dict to JSON string"""
    return json.dumps(d, separators=(",", ":"), ensure_ascii=False)

def from_json(s: str) -> dict:
    """Parse JSON string to dict, returns empty dict on error"""
    try:
        return {} if not s else json.loads(s)
    except Exception:
        return {}
