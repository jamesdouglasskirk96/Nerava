"""
Schemas for Merchant Details API
"""
from pydantic import BaseModel
from typing import Optional, List


class MerchantInfo(BaseModel):
    id: str
    name: str
    category: str
    photo_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None  # Multiple photos
    address: Optional[str] = None
    rating: Optional[float] = None
    user_rating_count: Optional[int] = None
    price_level: Optional[int] = None
    description: Optional[str] = None
    hours_today: Optional[str] = None  # e.g., "11 AM–11 PM"
    open_now: Optional[bool] = None
    weekday_hours: Optional[List[str]] = None  # Full week schedule

    class Config:
        from_attributes = True


class MomentInfo(BaseModel):
    label: str
    distance_miles: float
    moment_copy: str


class PerkInfo(BaseModel):
    title: str
    badge: str
    description: str
    options: Optional[str] = None  # e.g., "Soda, Coffee, or Margarita"


class WalletInfo(BaseModel):
    can_add: bool
    state: str  # "INACTIVE" | "ACTIVE"
    active_copy: Optional[str] = None


class ActionsInfo(BaseModel):
    add_to_wallet: bool
    get_directions_url: Optional[str] = None


class MerchantDetailsResponse(BaseModel):
    merchant: MerchantInfo
    moment: MomentInfo
    perk: PerkInfo
    wallet: WalletInfo
    actions: ActionsInfo

