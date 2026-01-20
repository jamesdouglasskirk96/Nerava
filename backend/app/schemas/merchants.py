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
    photo_urls: Optional[List[str]] = None
    description: Optional[str] = None
    hours_today: Optional[str] = None  # e.g., "11 AM-11 PM · Open now"
    address: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    activations_today: Optional[int] = 0
    verified_visits_today: Optional[int] = 0

    class Config:
        from_attributes = True


class MomentInfo(BaseModel):
    label: Optional[str] = None
    distance_miles: float
    moment_copy: str


class PerkInfo(BaseModel):
    title: str
    badge: str
    description: str


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
    perk: Optional[PerkInfo] = None  # Only merchants with exclusive offers have perks
    wallet: WalletInfo
    actions: ActionsInfo

