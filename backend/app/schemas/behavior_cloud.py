"""
Pydantic models for Behavior Cloud API.
"""
from pydantic import BaseModel
from typing import List, Dict, Any
from datetime import datetime

class Segment(BaseModel):
    name: str
    size: int
    avg_shift_kwh: float
    elasticity: float

class Participation(BaseModel):
    total_users: int
    active_participants: int
    participation_rate: float
    avg_shift_kwh: float

class Elasticity(BaseModel):
    price_elasticity: float
    time_elasticity: float
    incentive_elasticity: float
    confidence: float

class BehaviorCloudResponse(BaseModel):
    utility_id: str
    window: str
    segments: List[Segment]
    participation: Participation
    elasticity: Elasticity
    generated_at: datetime
