"""
Demo Square Endpoints

Swagger-driven demo endpoints for creating Square sandbox orders and payments.
Only enabled when DEMO_MODE=true and requires X-Demo-Admin-Key header.
"""
from fastapi import APIRouter, Depends, HTTPException, status, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session
from typing import Optional
import logging

from ..db import get_db
from ..models.domain import DomainMerchant
from ..services.square_orders import (
    create_order,
    create_payment_for_order,
    SquareNotConnectedError,
    SquareError
)
from ..core.config import settings
import os

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/demo/square", tags=["demo-square"])


def verify_demo_admin_key(x_demo_admin_key: Optional[str] = Header(None)) -> None:
    """
    Verify demo admin key header.
    
    Raises:
        HTTPException: If DEMO_MODE is not enabled or key is missing/wrong
    """
    if not settings.DEMO_MODE:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Demo mode is not enabled"
        )
    
    demo_admin_key = os.getenv("DEMO_ADMIN_KEY", "")
    if not demo_admin_key:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="DEMO_ADMIN_KEY not configured"
        )
    
    if not x_demo_admin_key or x_demo_admin_key != demo_admin_key:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing X-Demo-Admin-Key header"
        )


class CreateOrderRequest(BaseModel):
    """Request to create a Square order"""
    merchant_id: str
    amount_cents: int
    name: str = "Coffee"


class CreateOrderResponse(BaseModel):
    """Response from order creation"""
    order_id: str
    total_cents: int
    created_at: str


class CreatePaymentRequest(BaseModel):
    """Request to create a Square payment"""
    merchant_id: str
    order_id: str
    amount_cents: int


class CreatePaymentResponse(BaseModel):
    """Response from payment creation"""
    payment_id: str
    status: str


@router.post("/orders/create", response_model=CreateOrderResponse)
async def create_square_order(
    request: CreateOrderRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_demo_admin_key)
):
    """
    Create a Square order (for Swagger demo).
    
    Requires:
    - DEMO_MODE=true
    - X-Demo-Admin-Key header with valid key
    
    Args:
        request: CreateOrderRequest with merchant_id, amount_cents, and optional name
        db: Database session
        
    Returns:
        CreateOrderResponse with order_id, total_cents, and created_at
    """
    # Get merchant
    merchant = db.query(DomainMerchant).filter(
        DomainMerchant.id == request.merchant_id
    ).first()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {request.merchant_id} not found"
            }
        )
    
    try:
        result = create_order(
            db,
            merchant,
            request.amount_cents,
            request.name
        )
        
        return CreateOrderResponse(
            order_id=result["order_id"],
            total_cents=result["total_cents"],
            created_at=result["created_at"]
        )
    except SquareNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "SQUARE_NOT_CONNECTED",
                "message": "Merchant is not connected to Square"
            }
        )
    except SquareError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SQUARE_API_ERROR",
                "message": str(e)
            }
        )


@router.post("/payments/create", response_model=CreatePaymentResponse)
async def create_square_payment(
    request: CreatePaymentRequest,
    db: Session = Depends(get_db),
    _: None = Depends(verify_demo_admin_key)
):
    """
    Create a Square payment for an order (for Swagger demo).
    
    Requires:
    - DEMO_MODE=true
    - X-Demo-Admin-Key header with valid key
    
    Args:
        request: CreatePaymentRequest with merchant_id, order_id, and amount_cents
        db: Database session
        
    Returns:
        CreatePaymentResponse with payment_id and status
    """
    # Get merchant
    merchant = db.query(DomainMerchant).filter(
        DomainMerchant.id == request.merchant_id
    ).first()
    
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "error": "MERCHANT_NOT_FOUND",
                "message": f"Merchant {request.merchant_id} not found"
            }
        )
    
    try:
        result = create_payment_for_order(
            db,
            merchant,
            request.order_id,
            request.amount_cents
        )
        
        return CreatePaymentResponse(
            payment_id=result["payment_id"],
            status=result["status"]
        )
    except SquareNotConnectedError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "SQUARE_NOT_CONNECTED",
                "message": "Merchant is not connected to Square"
            }
        )
    except SquareError as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={
                "error": "SQUARE_API_ERROR",
                "message": str(e)
            }
        )

