"""
Merchant Onboarding Router

Handles merchant onboarding endpoints:
- Google Business Profile OAuth
- Location claims
- Stripe SetupIntent for card-on-file
- Placement rule updates
"""
import logging
import secrets
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import User
from app.dependencies_domain import get_current_user
from app.schemas.merchant_onboarding import (
    GoogleAuthStartRequest,
    GoogleAuthStartResponse,
    GoogleAuthCallbackRequest,
    GoogleAuthCallbackResponse,
    LocationsListResponse,
    LocationSummary,
    ClaimLocationRequest,
    ClaimLocationResponse,
    SetupIntentRequest,
    SetupIntentResponse,
    UpdatePlacementRequest,
    UpdatePlacementResponse,
)
from app.services.google_business_profile import (
    get_oauth_authorize_url,
    exchange_oauth_code,
    list_locations,
)
from app.services.merchant_onboarding_service import (
    create_or_get_merchant_account,
    store_oauth_state,
    validate_oauth_state,
    claim_location,
    create_setup_intent,
    update_placement_rule,
)
from app.core.config import settings

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1/merchant", tags=["merchant_onboarding"])


@router.post(
    "/auth/google/start",
    response_model=GoogleAuthStartResponse,
    summary="Start Google Business Profile OAuth",
    description="""
    Initiate Google Business Profile OAuth flow for merchant onboarding.
    
    Returns authorization URL and state token for CSRF protection.
    Frontend should redirect user to auth_url.
    """
)
async def start_google_auth(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Start Google Business Profile OAuth flow.
    """
    try:
        # Generate state token for CSRF protection
        state = secrets.token_urlsafe(32)
        store_oauth_state(state, current_user.id)
        
        # Build redirect URI
        redirect_uri = f"{settings.FRONTEND_URL}/merchant/auth/google/callback"
        
        # Get authorization URL
        auth_url = get_oauth_authorize_url(state, redirect_uri)
        
        return GoogleAuthStartResponse(
            auth_url=auth_url,
            state=state,
        )
    except Exception as e:
        logger.error(f"Error starting Google OAuth: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to start Google OAuth",
        )


@router.get(
    "/auth/google/callback",
    response_model=GoogleAuthCallbackResponse,
    summary="Handle Google OAuth callback",
    description="""
    Handle Google OAuth callback and store access token.
    
    This endpoint is called by Google after user authorizes.
    Stores encrypted token (or short-lived for dev).
    """
)
async def google_auth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="OAuth state token"),
    db: Session = Depends(get_db),
):
    """
    Handle Google OAuth callback.
    """
    try:
        # Validate state
        user_id = validate_oauth_state(state)
        if not user_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid or expired OAuth state",
            )
        
        # Exchange code for tokens
        redirect_uri = f"{settings.FRONTEND_URL}/merchant/auth/google/callback"
        tokens = await exchange_oauth_code(code, redirect_uri)
        
        # Create or get merchant account
        merchant_account = create_or_get_merchant_account(db, user_id)
        
        # TODO: Store encrypted tokens in database
        # For now, we'll just create the account
        # In production, create a MerchantOAuthToken model to store encrypted tokens
        
        logger.info(f"Google OAuth completed for merchant account {merchant_account.id}")
        
        return GoogleAuthCallbackResponse(
            success=True,
            merchant_account_id=merchant_account.id,
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error handling Google OAuth callback: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to handle Google OAuth callback",
        )


@router.get(
    "/locations",
    response_model=LocationsListResponse,
    summary="List Google Business Profile locations",
    description="""
    List available Google Business Profile locations for the authenticated merchant.
    
    In mock mode (MERCHANT_AUTH_MOCK=true), returns seeded fake locations.
    """
)
async def list_merchant_locations(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    List available locations for the merchant.
    """
    try:
        # Get merchant account
        merchant_account = create_or_get_merchant_account(db, current_user.id)
        
        # TODO: Get access token from stored OAuth tokens
        # For now, use mock token in mock mode
        access_token = "mock_token" if settings.MERCHANT_AUTH_MOCK else None
        
        if not access_token:
            # In real mode, we'd fetch from stored tokens
            # For now, raise error if not in mock mode
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="OAuth not completed. Please complete Google OAuth flow first.",
            )
        
        # List locations
        locations_data = await list_locations(access_token)
        
        locations = [
            LocationSummary(
                location_id=loc.get("location_id", ""),
                name=loc.get("name", ""),
                address=loc.get("address", ""),
                place_id=loc.get("place_id"),
            )
            for loc in locations_data
        ]
        
        return LocationsListResponse(locations=locations)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error listing locations: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to list locations",
        )


@router.post(
    "/claim",
    response_model=ClaimLocationResponse,
    summary="Claim a location",
    description="""
    Claim a Google Place location for the merchant account.
    
    Creates a MerchantLocationClaim record.
    """
)
async def claim_location_endpoint(
    request: ClaimLocationRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Claim a location for the merchant account.
    """
    try:
        # Get merchant account
        merchant_account = create_or_get_merchant_account(db, current_user.id)
        
        # Claim location
        claim = claim_location(
            db=db,
            merchant_account_id=merchant_account.id,
            place_id=request.place_id,
        )
        
        return ClaimLocationResponse(
            claim_id=claim.id,
            place_id=claim.place_id,
            status=claim.status,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error claiming location: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to claim location",
        )


@router.post(
    "/billing/setup_intent",
    response_model=SetupIntentResponse,
    summary="Create Stripe SetupIntent",
    description="""
    Create Stripe SetupIntent for card-on-file collection.
    
    Returns client_secret for frontend to complete card setup.
    Does not charge the card - only collects for future use.
    """
)
async def create_setup_intent_endpoint(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Create Stripe SetupIntent for card-on-file.
    """
    try:
        # Get merchant account
        merchant_account = create_or_get_merchant_account(db, current_user.id)
        
        # Create SetupIntent
        result = create_setup_intent(db, merchant_account.id)
        
        return SetupIntentResponse(
            client_secret=result["client_secret"],
            setup_intent_id=result["setup_intent_id"],
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error creating SetupIntent: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create SetupIntent",
        )


@router.post(
    "/placement/update",
    response_model=UpdatePlacementResponse,
    summary="Update placement rules",
    description="""
    Update placement rules for a claimed location.
    
    Requires:
    - Location must be claimed by merchant
    - Active payment method must exist
    
    Updates boost_weight (additive), daily_cap_cents, and perks_enabled.
    """
)
async def update_placement_endpoint(
    request: UpdatePlacementRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Update placement rules for a location.
    """
    try:
        # Get merchant account
        merchant_account = create_or_get_merchant_account(db, current_user.id)
        
        # Update placement rule
        rule = update_placement_rule(
            db=db,
            merchant_account_id=merchant_account.id,
            place_id=request.place_id,
            daily_cap_cents=request.daily_cap_cents,
            boost_weight=request.boost_weight,
            perks_enabled=request.perks_enabled,
        )
        
        return UpdatePlacementResponse(
            rule_id=rule.id,
            place_id=rule.place_id,
            status=rule.status,
            daily_cap_cents=rule.daily_cap_cents,
            boost_weight=rule.boost_weight,
            perks_enabled=rule.perks_enabled,
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e),
        )
    except Exception as e:
        logger.error(f"Error updating placement: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to update placement",
        )



