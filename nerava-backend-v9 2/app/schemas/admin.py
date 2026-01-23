"""
Admin API Schemas
Request and response models for admin endpoints
"""
from pydantic import BaseModel, Field
from typing import Optional, List, Literal
from datetime import datetime


class AdminLoginRequest(BaseModel):
    email: str
    password: str


class AdminLoginResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    admin_email: str


class ToggleExclusiveRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Mandatory reason for toggle")


class ToggleExclusiveResponse(BaseModel):
    exclusive_id: str
    previous_state: bool
    new_state: bool
    toggled_by: str
    reason: str


class AdminExclusiveItem(BaseModel):
    id: str
    merchant_id: str
    merchant_name: str
    title: str
    description: Optional[str]
    nova_reward: int
    is_active: bool
    daily_cap: Optional[int]
    activations_today: int
    activations_this_month: int
    created_at: datetime
    updated_at: datetime


class AdminExclusivesResponse(BaseModel):
    exclusives: List[AdminExclusiveItem]
    total: int
    limit: int
    offset: int


class MerchantActionRequest(BaseModel):
    reason: str = Field(..., min_length=5, description="Mandatory reason for action")


class MerchantActionResponse(BaseModel):
    merchant_id: str
    action: str
    previous_status: str
    new_status: str
    reason: str


class ForceCloseRequest(BaseModel):
    location_id: str
    reason: str = Field(..., min_length=10, description="Mandatory reason for force close")


class ForceCloseResponse(BaseModel):
    location_id: str
    sessions_closed: int
    closed_by: str
    reason: str
    timestamp: datetime


class EmergencyPauseRequest(BaseModel):
    action: Literal["activate", "deactivate"]
    reason: str = Field(..., min_length=10)
    confirmation: str = Field(..., description="Must be 'CONFIRM-EMERGENCY-PAUSE'")


class EmergencyPauseResponse(BaseModel):
    action: str
    activated_by: str
    reason: str
    timestamp: datetime


class AdminLogEntry(BaseModel):
    id: str
    operator_id: int
    operator_email: Optional[str]
    action_type: str
    target_type: str
    target_id: str
    reason: Optional[str]
    ip_address: Optional[str]
    created_at: datetime


class AdminLogsResponse(BaseModel):
    logs: List[AdminLogEntry]
    total: int
    limit: int
    offset: int

