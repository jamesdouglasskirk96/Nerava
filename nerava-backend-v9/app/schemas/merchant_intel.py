"""
Pydantic models for Merchant Intelligence API.
"""
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
from datetime import datetime

class Cohort(BaseModel):
    name: str
    size: int
    avg_monthly_spend: float
    retention_rate: float

class Forecast(BaseModel):
    expected_visits: int
    confidence: float
    peak_hours: List[str]

class Promo(BaseModel):
    id: str
    name: str
    discount_percent: int
    usage_count: int
    conversion_rate: float

class MerchantIntelOverviewResponse(BaseModel):
    merchant_id: str
    cohorts: List[Cohort]
    forecasts: Dict[str, Forecast]
    promos: Dict[str, List[Promo]]
    last_updated: datetime
