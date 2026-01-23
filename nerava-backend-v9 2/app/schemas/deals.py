"""
Pydantic models for Contextual Commerce API.
"""
from pydantic import BaseModel
from typing import List, Dict, Any

class Window(BaseModel):
    start: str
    end: str
    timezone: str

class Deal(BaseModel):
    merchant_id: str
    name: str
    discount_percent: int
    green_hour_bonus: int
    distance_m: int

class GreenHourDealsResponse(BaseModel):
    window: Window
    deals: List[Deal]
