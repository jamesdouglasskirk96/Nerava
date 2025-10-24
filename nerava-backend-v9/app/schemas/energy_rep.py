"""
Pydantic models for Energy Reputation API.
"""
from pydantic import BaseModel
from typing import Dict, Any
from datetime import datetime

class EnergyRepResponse(BaseModel):
    user_id: str
    score: int
    tier: str
    components: Dict[str, float]
    last_calculated_at: datetime
