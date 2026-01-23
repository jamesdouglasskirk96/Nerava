"""
Pilot Party Cluster endpoints for Charge Party flow
"""
import logging
from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from pydantic import BaseModel
from datetime import datetime

from app.db import get_db
from app.models.while_you_charge import ChargerCluster, Charger, ChargerMerchant, Merchant, MerchantPerk
from app.services.merchant_activation_counts import get_merchant_activation_counts

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/pilot/party", tags=["pilot-party"])


class MerchantCard(BaseModel):
    id: str
    name: str
    address: Optional[str] = None
    photo_url: Optional[str] = None
    photo_urls: Optional[List[str]] = None
    description: Optional[str] = None
    distance_to_charger: Optional[float] = None
    activations_today: int = 0
    verified_visits_today: int = 0
    offer_preview: Optional[Dict[str, Any]] = None
    is_primary: bool = False


class ClusterResponse(BaseModel):
    cluster_id: str
    charger_radius_m: int
    merchant_radius_m: int
    primary_merchant: MerchantCard
    merchants: List[MerchantCard]


@router.get("/cluster", response_model=ClusterResponse)
async def get_party_cluster(
    cluster_id: Optional[str] = Query(None, description="Cluster ID (optional, defaults to asadas_party)"),
    db: Session = Depends(get_db)
):
    """
    Get party cluster with Asadas as primary merchant and other seeded merchants.
    
    Returns cluster with:
    - charger_radius_m=400, merchant_radius_m=40
    - primary_merchant (Asadas, always first)
    - merchants array (includes Asadas + others)
    
    Args:
        cluster_id: Optional cluster ID. If not provided, defaults to "asadas_party" cluster.
    """
    # Query cluster by ID if provided, otherwise by name
    cluster = None
    if cluster_id:
        # Try by name first (e.g., "asadas_party"), then by UUID
        cluster = db.query(ChargerCluster).filter(ChargerCluster.name == cluster_id).first()
        if not cluster:
            # Try as UUID
            try:
                import uuid
                uuid.UUID(cluster_id)  # Validate it's a UUID
                cluster = db.query(ChargerCluster).filter(ChargerCluster.id == cluster_id).first()
            except (ValueError, AttributeError):
                pass  # Not a valid UUID, cluster remains None
    else:
        cluster = db.query(ChargerCluster).filter(ChargerCluster.name == "asadas_party").first()
    
    if not cluster:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Party cluster not found. Run bootstrap endpoint first."
        )
    
    # Get charger
    charger = db.query(Charger).filter(Charger.id == cluster.charger_id).first()
    if not charger:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Charger not found for cluster"
        )
    
    # Get primary merchant (Asadas) via ChargerMerchant.is_primary=True
    primary_link = db.query(ChargerMerchant).filter(
        ChargerMerchant.charger_id == charger.id,
        ChargerMerchant.is_primary == True
    ).first()
    
    if not primary_link:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Primary merchant not found for cluster"
        )
    
    primary_merchant = db.query(Merchant).filter(Merchant.id == primary_link.merchant_id).first()
    if not primary_merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Primary merchant record not found"
        )
    
    # Get other seeded merchants for cluster
    other_links = db.query(ChargerMerchant).filter(
        ChargerMerchant.charger_id == charger.id,
        ChargerMerchant.merchant_id != primary_merchant.id
    ).order_by(ChargerMerchant.distance_m.asc()).all()
    
    # Build merchant cards
    merchants_list = []
    
    # Add primary merchant first (always)
    primary_counts = get_merchant_activation_counts(db, primary_merchant.id)
    
    # Get offer preview (MerchantPerk)
    primary_perk = db.query(MerchantPerk).filter(
        MerchantPerk.merchant_id == primary_merchant.id,
        MerchantPerk.is_active == True
    ).first()
    
    offer_preview = None
    if primary_perk:
        offer_preview = {
            "title": primary_perk.title,
            "description": primary_perk.description,
            "nova_reward": primary_perk.nova_reward
        }
    
    primary_card = MerchantCard(
        id=primary_merchant.id,
        name=primary_merchant.name,
        address=primary_merchant.address,
        photo_url=primary_merchant.primary_photo_url or primary_merchant.photo_url,
        photo_urls=primary_merchant.photo_urls or [],
        description=primary_merchant.description or primary_merchant.category or "Restaurant",  # Use description from Google Places
        distance_to_charger=primary_link.distance_m,  # Accurate distance from ChargerMerchant
        activations_today=primary_counts["activations_today"],
        verified_visits_today=primary_counts["verified_visits_today"],
        offer_preview=offer_preview,
        is_primary=True
    )
    merchants_list.append(primary_card)
    
    # Add other merchants
    for link in other_links:
        merchant = db.query(Merchant).filter(Merchant.id == link.merchant_id).first()
        if not merchant:
            continue
        
        counts = get_merchant_activation_counts(db, merchant.id)
        
        # Get offer preview if exists
        perk = db.query(MerchantPerk).filter(
            MerchantPerk.merchant_id == merchant.id,
            MerchantPerk.is_active == True
        ).first()
        
        offer_preview = None
        if perk:
            offer_preview = {
                "title": perk.title,
                "description": perk.description,
                "nova_reward": perk.nova_reward
            }
        
        merchant_card = MerchantCard(
            id=merchant.id,
            name=merchant.name,
            address=merchant.address,
            photo_url=merchant.primary_photo_url or merchant.photo_url,
            photo_urls=merchant.photo_urls or [],
            description=merchant.description or merchant.category or merchant.primary_category or "Restaurant",  # Use description from Google Places
            distance_to_charger=link.distance_m,  # Accurate distance from ChargerMerchant
            activations_today=counts["activations_today"],
            verified_visits_today=counts["verified_visits_today"],
            offer_preview=offer_preview,
            is_primary=False
        )
        merchants_list.append(merchant_card)
    
    return ClusterResponse(
        cluster_id=str(cluster.id),
        charger_radius_m=cluster.charger_radius_m,
        merchant_radius_m=cluster.merchant_radius_m,
        primary_merchant=primary_card,
        merchants=merchants_list
    )


class VerifyVisitRequest(BaseModel):
    merchant_id: str
    lat: float
    lng: float


@router.post("/verify_visit")
async def verify_visit(
    request: VerifyVisitRequest,
    db: Session = Depends(get_db)
):
    """
    Verify a visit to a merchant (pilot party endpoint).
    
    This is a simplified version for the party flow that marks a visit as verified.
    """
    from app.models import User
    from app.services.verify_dwell import haversine_m
    from app.services.analytics import get_analytics_client
    
    # Get merchant
    merchant = db.query(Merchant).filter(Merchant.id == request.merchant_id).first()
    if not merchant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Merchant not found: {request.merchant_id}"
        )
    
    # Calculate distance to merchant
    distance_m = haversine_m(request.lat, request.lng, merchant.lat, merchant.lng)
    
    # For party flow, we'll just return success (visit verified)
    # In a real implementation, this would mark a visit as verified in the database
    
    # PostHog: Fire visit_verified event
    analytics = get_analytics_client()
    # Use a default user ID for party flow (or get from auth if available)
    distinct_id = f"party_user_{request.merchant_id}"
    
    analytics.capture(
        event="visit_verified",
        distinct_id=distinct_id,
        user_id=distinct_id,
        merchant_id=request.merchant_id,
        properties={
            "source": "driver",
            "cluster_id": None,  # Could be resolved from merchant if needed
            "distance_m": int(distance_m)
        }
    )
    
    return {
        "ok": True,
        "merchant_id": request.merchant_id,
        "distance_m": int(distance_m),
        "verified": True
    }


@router.get("/merchant/me")
async def get_merchant_me(
    email: str = Query(..., description="Merchant admin email"),
    db: Session = Depends(get_db)
):
    """
    Get merchant info for party flow (simplified auth for smoke test).
    
    This endpoint fires the merchant_portal_page_viewed event.
    """
    from app.models import User
    from app.services.analytics import get_analytics_client
    from app.models_domain import DomainMerchant
    
    # Find merchant user by email
    user = db.query(User).filter(User.email == email).first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"User not found for email: {email}"
        )
    
    # Find associated domain merchant
    domain_merchant = db.query(DomainMerchant).filter(
        DomainMerchant.owner_user_id == user.id
    ).first()
    
    merchant_id = str(domain_merchant.id) if domain_merchant else None
    
    # PostHog: Fire merchant_portal_page_viewed event
    analytics = get_analytics_client()
    analytics.capture(
        event="merchant_portal_page_viewed",
        distinct_id=user.public_id,
        user_id=user.public_id,
        merchant_id=merchant_id,
        properties={
            "source": "merchant",
            "cluster_id": None
        }
    )
    
    return {
        "merchant_id": merchant_id,
        "user_id": str(user.id),
        "email": user.email
    }

