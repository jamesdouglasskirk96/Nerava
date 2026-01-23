from __future__ import annotations
from typing import Dict, Any
import json


def emit(topic: str, payload: Dict[str, Any]) -> None:
    # Stub: structured log
    print(json.dumps({"topic": topic, "payload": payload}))


