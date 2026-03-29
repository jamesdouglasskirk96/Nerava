"""
Merchant ordering config endpoints.

Exposes POS ordering configuration for the driver app to build
WebView commerce screens.
"""
import logging
import secrets
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.dependencies import get_db
from app.models.while_you_charge import Merchant
from app.services.pos_adapter_service import POSAdapterFactory

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/ordering", tags=["ordering"])


class MerchantOrderingConfig(BaseModel):
    ordering_enabled: bool = False
    pos_type: Optional[str] = None
    ordering_url: Optional[str] = None
    discount_injection_method: Optional[str] = None
    discount_param_key: Optional[str] = None
    phone_field_selector: Optional[str] = None
    confirmation_url_pattern: Optional[str] = None
    nerava_offer: Optional[str] = None
    nerava_discount_code: Optional[str] = None


class BuildURLRequest(BaseModel):
    merchant_id: str
    session_id: str
    user_phone: Optional[str] = None


class BuildURLResponse(BaseModel):
    ordering_url: str
    pos_type: str
    nerava_offer: Optional[str] = None
    discount_code: Optional[str] = None
    phone_inject_js: str = ""
    discount_inject_js: str = ""
    confirmation_url_pattern: Optional[str] = None
    requires_manual_confirmation: bool = False


@router.get("/config/{merchant_place_id}", response_model=MerchantOrderingConfig)
def get_merchant_ordering_config(merchant_place_id: str, db: Session = Depends(get_db)):
    """Get ordering configuration for a merchant by place_id."""
    merchant = db.query(Merchant).filter(Merchant.place_id == merchant_place_id).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    return MerchantOrderingConfig(
        ordering_enabled=merchant.ordering_enabled,
        pos_type=merchant.pos_type,
        ordering_url=merchant.ordering_url,
        discount_injection_method=merchant.discount_injection_method,
        discount_param_key=merchant.discount_param_key,
        phone_field_selector=merchant.phone_field_selector,
        confirmation_url_pattern=merchant.confirmation_url_pattern,
        nerava_offer=merchant.nerava_offer,
        nerava_discount_code=merchant.nerava_discount_code,
    )


@router.post("/build-url", response_model=BuildURLResponse)
def build_ordering_url(req: BuildURLRequest, db: Session = Depends(get_db)):
    """Build the full ordering URL with UTM tracking, discount, and injection scripts."""
    merchant = db.query(Merchant).filter(
        (Merchant.place_id == req.merchant_id) | (Merchant.id == req.merchant_id)
    ).first()
    if not merchant:
        raise HTTPException(status_code=404, detail="Merchant not found")

    if not merchant.ordering_enabled or not merchant.ordering_url:
        raise HTTPException(status_code=400, detail="Ordering not enabled for this merchant")

    pos_type = merchant.pos_type or "other"
    adapter = POSAdapterFactory.get_adapter(pos_type)

    # Generate a session-specific discount code if merchant has one configured
    discount_code = merchant.nerava_discount_code
    if not discount_code and merchant.nerava_offer:
        discount_code = f"NRV-{secrets.token_hex(4).upper()}"

    url = adapter.build_ordering_url(
        ordering_url=merchant.ordering_url,
        session_id=req.session_id,
        user_phone=req.user_phone,
        discount_code=discount_code,
    )

    phone_js = ""
    if req.user_phone:
        phone_js = adapter.get_phone_inject_js(
            req.user_phone, merchant.phone_field_selector
        )

    discount_js = ""
    if discount_code:
        discount_js = adapter.get_discount_inject_js(
            discount_code, merchant.phone_field_selector
        )

    return BuildURLResponse(
        ordering_url=url,
        pos_type=pos_type,
        nerava_offer=merchant.nerava_offer,
        discount_code=discount_code,
        phone_inject_js=phone_js,
        discount_inject_js=discount_js,
        confirmation_url_pattern=merchant.confirmation_url_pattern,
        requires_manual_confirmation=(pos_type == "other"),
    )
