"""
Schemas for Merchant Details API
"""
from pydantic import BaseModel
from typing import Optional, List, Dict, Literal


class MerchantInfo(BaseModel):
    id: str
    name: str
    category: str
    photo_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    description: Optional[str] = None
    hours_today: Optional[str] = None  # e.g., "11 AM-11 PM · Open now"
    address: Optional[str] = None
    phone: Optional[str] = None
    website: Optional[str] = None
    rating: Optional[float] = None
    price_level: Optional[int] = None
    activations_today: Optional[int] = 0
    verified_visits_today: Optional[int] = 0
    amenities: Optional[Dict[str, Dict[str, int]]] = None  # {"bathroom": {"upvotes": 42, "downvotes": 3}, "wifi": {"upvotes": 38, "downvotes": 7}}
    place_id: Optional[str] = None  # Google Places ID

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


class AmenityVoteRequest(BaseModel):
    """Request schema for voting on an amenity"""
    vote_type: Literal['up', 'down']


class AmenityVoteResponse(BaseModel):
    """Response schema for amenity vote"""
    ok: bool
    upvotes: int
    downvotes: int

