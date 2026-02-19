# Implement Merchant Claim Flow (Email + Phone Verification)

**Date:** 2026-01-23
**Goal:** Replace incomplete Google OAuth with working dual-verification merchant onboarding
**Priority:** High - Unblocks merchant acquisition

---

## Context

The current merchant claim flow at `/claim/:businessId` is broken (Google OAuth incomplete). We need a working flow that:
1. Verifies the merchant owns the phone number (OTP)
2. Verifies the merchant owns the email (Magic Link)
3. Creates a merchant user account with `merchant_admin` role
4. Redirects to merchant dashboard

**Existing infrastructure to reuse:**
- `POST /v1/auth/otp/start` - Send phone OTP
- `POST /v1/auth/otp/verify` - Verify phone code
- `POST /v1/auth/magic_link/request` - Send magic link email
- `GET /v1/auth/magic_link/verify` - Verify magic link token

---

## Database Schema

### Create Claim Session Table

Create migration file: `backend/alembic/versions/xxxx_add_claim_sessions.py`

```python
"""Add claim_sessions table

Revision ID: add_claim_sessions
Revises: <previous_revision>
Create Date: 2026-01-23
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB
import uuid

revision = 'add_claim_sessions'
down_revision = '<GET_PREVIOUS_REVISION>'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table(
        'claim_sessions',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('business_id', UUID(as_uuid=True), sa.ForeignKey('businesses.id'), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('phone', sa.String(20), nullable=False),
        sa.Column('business_name', sa.String(255), nullable=False),
        sa.Column('phone_verified', sa.Boolean, default=False),
        sa.Column('email_verified', sa.Boolean, default=False),
        sa.Column('magic_link_token', sa.String(255), nullable=True),
        sa.Column('magic_link_expires_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime(timezone=True), onupdate=sa.func.now()),
        sa.Column('completed_at', sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index('ix_claim_sessions_business_id', 'claim_sessions', ['business_id'])
    op.create_index('ix_claim_sessions_magic_link_token', 'claim_sessions', ['magic_link_token'])
    op.create_index('ix_claim_sessions_email', 'claim_sessions', ['email'])

def downgrade():
    op.drop_table('claim_sessions')
```

### Create SQLAlchemy Model

File: `backend/app/models/claim_session.py`

```python
"""Claim session model for merchant onboarding"""
from sqlalchemy import Column, String, Boolean, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.sql import func
import uuid

from ..db.base_class import Base


class ClaimSession(Base):
    __tablename__ = "claim_sessions"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    business_id = Column(UUID(as_uuid=True), ForeignKey("businesses.id"), nullable=False)
    email = Column(String(255), nullable=False)
    phone = Column(String(20), nullable=False)
    business_name = Column(String(255), nullable=False)
    phone_verified = Column(Boolean, default=False)
    email_verified = Column(Boolean, default=False)
    magic_link_token = Column(String(255), nullable=True, index=True)
    magic_link_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)
```

Add to `backend/app/models/__init__.py`:
```python
from .claim_session import ClaimSession
```

---

## Backend API Endpoints

### Create Router

File: `backend/app/routers/merchant_claim.py`

```python
"""Merchant claim flow endpoints"""
from datetime import datetime, timedelta, timezone
from typing import Optional
import secrets
import logging

from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from ..db.session import get_db
from ..models.claim_session import ClaimSession
from ..models.user import User
from ..models.business import Business
from ..services.otp_service_v2 import otp_service
from ..services.email_service import send_magic_link_email
from ..core.security import create_access_token, create_refresh_token
from ..utils.phone import normalize_phone

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/v1/merchant/claim", tags=["merchant-claim"])

MAGIC_LINK_EXPIRY_MINUTES = 15


# Request/Response Models
class ClaimStartRequest(BaseModel):
    business_id: str
    email: EmailStr
    phone: str
    business_name: str


class ClaimStartResponse(BaseModel):
    session_id: str
    message: str


class VerifyPhoneRequest(BaseModel):
    session_id: str
    code: str


class VerifyPhoneResponse(BaseModel):
    phone_verified: bool
    message: str


class SendMagicLinkRequest(BaseModel):
    session_id: str


class SendMagicLinkResponse(BaseModel):
    email_sent: bool
    message: str


class VerifyMagicLinkResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    user: dict


# Endpoints
@router.post("/start", response_model=ClaimStartResponse)
async def start_claim(
    request: ClaimStartRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 1: Start claim process
    - Validate business exists and is not claimed
    - Create claim session
    - Send OTP to phone
    """
    # Validate business exists
    business = await db.get(Business, request.business_id)
    if not business:
        raise HTTPException(status_code=404, detail="Business not found")

    # Check if already claimed
    if business.owner_id:
        raise HTTPException(status_code=400, detail="Business already claimed")

    # Normalize phone
    phone = normalize_phone(request.phone)
    if not phone:
        raise HTTPException(status_code=400, detail="Invalid phone number")

    # Check for existing pending session
    existing = await db.execute(
        select(ClaimSession).where(
            ClaimSession.business_id == request.business_id,
            ClaimSession.completed_at.is_(None)
        )
    )
    existing_session = existing.scalar_one_or_none()

    if existing_session:
        # Update existing session
        existing_session.email = request.email
        existing_session.phone = phone
        existing_session.phone_verified = False
        existing_session.email_verified = False
        session = existing_session
    else:
        # Create new session
        session = ClaimSession(
            business_id=request.business_id,
            email=request.email,
            phone=phone,
            business_name=request.business_name,
        )
        db.add(session)

    await db.commit()
    await db.refresh(session)

    # Send OTP
    try:
        await otp_service.send_otp(phone)
        logger.info(f"[ClaimFlow] OTP sent to {phone[-4:]}")
    except Exception as e:
        logger.error(f"[ClaimFlow] Failed to send OTP: {e}")
        raise HTTPException(status_code=500, detail="Failed to send verification code")

    return ClaimStartResponse(
        session_id=str(session.id),
        message="Verification code sent to your phone"
    )


@router.post("/verify-phone", response_model=VerifyPhoneResponse)
async def verify_phone(
    request: VerifyPhoneRequest,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 2: Verify phone OTP
    """
    session = await db.get(ClaimSession, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session already completed")

    # Verify OTP
    is_valid = await otp_service.verify_otp(session.phone, request.code)

    if not is_valid:
        raise HTTPException(status_code=400, detail="Invalid verification code")

    session.phone_verified = True
    await db.commit()

    logger.info(f"[ClaimFlow] Phone verified for session {session.id}")

    return VerifyPhoneResponse(
        phone_verified=True,
        message="Phone verified successfully"
    )


@router.post("/send-magic-link", response_model=SendMagicLinkResponse)
async def send_magic_link(
    request: SendMagicLinkRequest,
    background_tasks: BackgroundTasks,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 3: Send magic link email (requires phone verified)
    """
    session = await db.get(ClaimSession, request.session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    if session.completed_at:
        raise HTTPException(status_code=400, detail="Session already completed")

    if not session.phone_verified:
        raise HTTPException(status_code=400, detail="Phone not verified")

    # Generate magic link token
    token = secrets.token_urlsafe(32)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=MAGIC_LINK_EXPIRY_MINUTES)

    session.magic_link_token = token
    session.magic_link_expires_at = expires_at
    await db.commit()

    # Send email
    magic_link_url = f"https://merchant.nerava.network/claim/verify?token={token}"

    background_tasks.add_task(
        send_magic_link_email,
        to_email=session.email,
        business_name=session.business_name,
        magic_link_url=magic_link_url
    )

    logger.info(f"[ClaimFlow] Magic link sent to {session.email}")

    return SendMagicLinkResponse(
        email_sent=True,
        message=f"Magic link sent to {session.email}"
    )


@router.get("/verify-magic-link", response_model=VerifyMagicLinkResponse)
async def verify_magic_link(
    token: str,
    db: AsyncSession = Depends(get_db)
):
    """
    Step 4: Verify magic link and create merchant account
    """
    # Find session by token
    result = await db.execute(
        select(ClaimSession).where(ClaimSession.magic_link_token == token)
    )
    session = result.scalar_one_or_none()

    if not session:
        raise HTTPException(status_code=400, detail="Invalid or expired link")

    if session.completed_at:
        raise HTTPException(status_code=400, detail="Link already used")

    if session.magic_link_expires_at < datetime.now(timezone.utc):
        raise HTTPException(status_code=400, detail="Link expired")

    if not session.phone_verified:
        raise HTTPException(status_code=400, detail="Phone not verified")

    # Check if user exists
    result = await db.execute(
        select(User).where(
            (User.email == session.email) | (User.phone == session.phone)
        )
    )
    user = result.scalar_one_or_none()

    if not user:
        # Create new user
        user = User(
            email=session.email,
            phone=session.phone,
            role_flags=["merchant_admin"],
            email_verified=True,
            phone_verified=True,
        )
        db.add(user)
        await db.flush()
        logger.info(f"[ClaimFlow] Created merchant user {user.id}")
    else:
        # Update existing user
        if "merchant_admin" not in (user.role_flags or []):
            user.role_flags = (user.role_flags or []) + ["merchant_admin"]
        logger.info(f"[ClaimFlow] Updated existing user {user.id} with merchant_admin role")

    # Claim the business
    business = await db.get(Business, session.business_id)
    business.owner_id = user.id

    # Mark session complete
    session.email_verified = True
    session.completed_at = datetime.now(timezone.utc)

    await db.commit()

    # Generate tokens
    access_token = create_access_token(subject=str(user.id))
    refresh_token = create_refresh_token(subject=str(user.id))

    logger.info(f"[ClaimFlow] Business {session.business_id} claimed by user {user.id}")

    return VerifyMagicLinkResponse(
        access_token=access_token,
        refresh_token=refresh_token,
        user={
            "id": str(user.id),
            "email": user.email,
            "phone": user.phone,
            "role_flags": user.role_flags,
        }
    )


@router.get("/session/{session_id}")
async def get_session_status(
    session_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Get claim session status"""
    session = await db.get(ClaimSession, session_id)
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    return {
        "session_id": str(session.id),
        "business_name": session.business_name,
        "phone_verified": session.phone_verified,
        "email_verified": session.email_verified,
        "completed": session.completed_at is not None,
    }
```

### Register Router

In `backend/app/main.py`, add:

```python
from .routers import merchant_claim

app.include_router(merchant_claim.router)
```

### Add Email Template

File: `backend/app/services/email_service.py` - Add function:

```python
async def send_magic_link_email(to_email: str, business_name: str, magic_link_url: str):
    """Send magic link email for merchant claim"""
    subject = f"Complete your {business_name} claim on Nerava"

    html_content = f"""
    <html>
    <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
        <h2>Complete Your Business Claim</h2>
        <p>You're almost done claiming <strong>{business_name}</strong> on Nerava!</p>
        <p>Click the button below to complete your claim and access your merchant dashboard:</p>
        <p style="text-align: center; margin: 30px 0;">
            <a href="{magic_link_url}"
               style="background-color: #10B981; color: white; padding: 12px 24px;
                      text-decoration: none; border-radius: 6px; font-weight: bold;">
                Complete Claim
            </a>
        </p>
        <p style="color: #666; font-size: 14px;">
            This link expires in 15 minutes. If you didn't request this, please ignore this email.
        </p>
        <p style="color: #999; font-size: 12px;">— The Nerava Team</p>
    </body>
    </html>
    """

    # Use existing email sending infrastructure (SES, SendGrid, etc.)
    await send_email(to_email, subject, html_content)
```

---

## Frontend Implementation

### Update ClaimBusiness Component

File: `apps/merchant/src/components/ClaimBusiness/ClaimBusiness.tsx`

```typescript
import { useState } from 'react'
import { useParams, useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { api } from '../../lib/api'

type ClaimStep = 'form' | 'verify-phone' | 'verify-email' | 'success'

interface ClaimFormData {
  businessName: string
  email: string
  phone: string
}

export function ClaimBusiness() {
  const { businessId } = useParams<{ businessId: string }>()
  const navigate = useNavigate()

  const [step, setStep] = useState<ClaimStep>('form')
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [formData, setFormData] = useState<ClaimFormData>({
    businessName: '',
    email: '',
    phone: '',
  })
  const [otpCode, setOtpCode] = useState('')
  const [error, setError] = useState<string | null>(null)

  // Step 1: Start claim
  const startClaim = useMutation({
    mutationFn: async (data: ClaimFormData) => {
      const response = await api.post('/v1/merchant/claim/start', {
        business_id: businessId,
        email: data.email,
        phone: data.phone,
        business_name: data.businessName,
      })
      return response.data
    },
    onSuccess: (data) => {
      setSessionId(data.session_id)
      setStep('verify-phone')
      setError(null)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to start claim')
    },
  })

  // Step 2: Verify phone
  const verifyPhone = useMutation({
    mutationFn: async (code: string) => {
      const response = await api.post('/v1/merchant/claim/verify-phone', {
        session_id: sessionId,
        code,
      })
      return response.data
    },
    onSuccess: () => {
      setStep('verify-email')
      sendMagicLink.mutate()
      setError(null)
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Invalid code')
    },
  })

  // Step 3: Send magic link
  const sendMagicLink = useMutation({
    mutationFn: async () => {
      const response = await api.post('/v1/merchant/claim/send-magic-link', {
        session_id: sessionId,
      })
      return response.data
    },
    onError: (err: any) => {
      setError(err.response?.data?.detail || 'Failed to send email')
    },
  })

  const handleFormSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    startClaim.mutate(formData)
  }

  const handleVerifyPhone = (e: React.FormEvent) => {
    e.preventDefault()
    verifyPhone.mutate(otpCode)
  }

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center p-4">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8">
        {/* Progress indicator */}
        <div className="flex justify-between mb-8">
          {['form', 'verify-phone', 'verify-email'].map((s, i) => (
            <div
              key={s}
              className={`w-8 h-8 rounded-full flex items-center justify-center text-sm font-medium
                ${step === s ? 'bg-green-500 text-white' :
                  ['form', 'verify-phone', 'verify-email'].indexOf(step) > i
                    ? 'bg-green-200 text-green-800'
                    : 'bg-gray-200 text-gray-500'}`}
            >
              {i + 1}
            </div>
          ))}
        </div>

        {error && (
          <div className="mb-4 p-3 bg-red-50 border border-red-200 text-red-700 rounded">
            {error}
          </div>
        )}

        {/* Step 1: Form */}
        {step === 'form' && (
          <form onSubmit={handleFormSubmit}>
            <h2 className="text-2xl font-bold mb-6">Claim Your Business</h2>

            <div className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Business Name
                </label>
                <input
                  type="text"
                  required
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                  value={formData.businessName}
                  onChange={(e) => setFormData({ ...formData, businessName: e.target.value })}
                  placeholder="Your Business Name"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Email Address
                </label>
                <input
                  type="email"
                  required
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                  value={formData.email}
                  onChange={(e) => setFormData({ ...formData, email: e.target.value })}
                  placeholder="you@business.com"
                />
              </div>

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">
                  Phone Number
                </label>
                <input
                  type="tel"
                  required
                  className="w-full px-3 py-2 border rounded-lg focus:ring-2 focus:ring-green-500"
                  value={formData.phone}
                  onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                  placeholder="+1 (555) 123-4567"
                />
              </div>
            </div>

            <button
              type="submit"
              disabled={startClaim.isPending}
              className="w-full mt-6 py-3 bg-green-500 text-white rounded-lg font-medium
                hover:bg-green-600 disabled:opacity-50"
            >
              {startClaim.isPending ? 'Sending code...' : 'Continue'}
            </button>
          </form>
        )}

        {/* Step 2: Verify Phone */}
        {step === 'verify-phone' && (
          <form onSubmit={handleVerifyPhone}>
            <h2 className="text-2xl font-bold mb-2">Verify Your Phone</h2>
            <p className="text-gray-600 mb-6">
              Enter the 6-digit code sent to {formData.phone}
            </p>

            <input
              type="text"
              inputMode="numeric"
              pattern="[0-9]*"
              maxLength={6}
              required
              className="w-full px-3 py-4 text-center text-2xl tracking-widest border rounded-lg
                focus:ring-2 focus:ring-green-500"
              value={otpCode}
              onChange={(e) => setOtpCode(e.target.value.replace(/\D/g, ''))}
              placeholder="000000"
              autoFocus
            />

            <button
              type="submit"
              disabled={verifyPhone.isPending || otpCode.length !== 6}
              className="w-full mt-6 py-3 bg-green-500 text-white rounded-lg font-medium
                hover:bg-green-600 disabled:opacity-50"
            >
              {verifyPhone.isPending ? 'Verifying...' : 'Verify Code'}
            </button>

            <button
              type="button"
              onClick={() => startClaim.mutate(formData)}
              className="w-full mt-2 py-2 text-green-600 text-sm"
            >
              Resend code
            </button>
          </form>
        )}

        {/* Step 3: Check Email */}
        {step === 'verify-email' && (
          <div className="text-center">
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2}
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z" />
              </svg>
            </div>

            <h2 className="text-2xl font-bold mb-2">Check Your Email</h2>
            <p className="text-gray-600 mb-6">
              We sent a magic link to <strong>{formData.email}</strong>
            </p>
            <p className="text-sm text-gray-500">
              Click the link in your email to complete the claim process.
              The link expires in 15 minutes.
            </p>

            <button
              type="button"
              onClick={() => sendMagicLink.mutate()}
              disabled={sendMagicLink.isPending}
              className="mt-6 text-green-600 text-sm"
            >
              {sendMagicLink.isPending ? 'Sending...' : 'Resend email'}
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
```

### Add Magic Link Verification Page

File: `apps/merchant/src/pages/ClaimVerify.tsx`

```typescript
import { useEffect, useState } from 'react'
import { useSearchParams, useNavigate } from 'react-router-dom'
import { api } from '../lib/api'
import { useAuth } from '../hooks/useAuth'

export function ClaimVerify() {
  const [searchParams] = useSearchParams()
  const navigate = useNavigate()
  const { setTokens } = useAuth()

  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const token = searchParams.get('token')
    if (!token) {
      setStatus('error')
      setError('Invalid link')
      return
    }

    api.get(`/v1/merchant/claim/verify-magic-link?token=${token}`)
      .then((response) => {
        setTokens(response.data.access_token, response.data.refresh_token)
        setStatus('success')
        // Redirect to dashboard after 2 seconds
        setTimeout(() => navigate('/dashboard'), 2000)
      })
      .catch((err) => {
        setStatus('error')
        setError(err.response?.data?.detail || 'Failed to verify link')
      })
  }, [searchParams])

  return (
    <div className="min-h-screen bg-gray-50 flex items-center justify-center">
      <div className="max-w-md w-full bg-white rounded-lg shadow-lg p-8 text-center">
        {status === 'loading' && (
          <>
            <div className="w-12 h-12 border-4 border-green-500 border-t-transparent rounded-full animate-spin mx-auto mb-4" />
            <p className="text-gray-600">Verifying your claim...</p>
          </>
        )}

        {status === 'success' && (
          <>
            <div className="w-16 h-16 bg-green-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-green-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Claim Complete!</h2>
            <p className="text-gray-600">Redirecting to your dashboard...</p>
          </>
        )}

        {status === 'error' && (
          <>
            <div className="w-16 h-16 bg-red-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <svg className="w-8 h-8 text-red-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
              </svg>
            </div>
            <h2 className="text-2xl font-bold text-gray-900 mb-2">Verification Failed</h2>
            <p className="text-gray-600">{error}</p>
            <button
              onClick={() => navigate('/claim')}
              className="mt-4 text-green-600"
            >
              Try again
            </button>
          </>
        )}
      </div>
    </div>
  )
}
```

### Update Routes

File: `apps/merchant/src/App.tsx` - Add routes:

```typescript
import { ClaimBusiness } from './components/ClaimBusiness/ClaimBusiness'
import { ClaimVerify } from './pages/ClaimVerify'

// In router config:
<Route path="/claim/:businessId" element={<ClaimBusiness />} />
<Route path="/claim/verify" element={<ClaimVerify />} />
```

---

## Testing

### Backend Tests

```bash
# Run migrations
cd backend
alembic upgrade head

# Start server
uvicorn app.main:app --reload

# Test endpoints
curl -X POST http://localhost:8000/v1/merchant/claim/start \
  -H "Content-Type: application/json" \
  -d '{"business_id": "test-uuid", "email": "test@example.com", "phone": "+17133056318", "business_name": "Test Business"}'
```

### Frontend Tests

```bash
cd apps/merchant
npm run dev
# Navigate to http://localhost:3000/claim/test-business-id
```

---

## Verification Checklist

- [ ] Database migration runs successfully
- [ ] ClaimSession model works with SQLAlchemy
- [ ] `/v1/merchant/claim/start` sends OTP
- [ ] `/v1/merchant/claim/verify-phone` validates OTP
- [ ] `/v1/merchant/claim/send-magic-link` sends email
- [ ] `/v1/merchant/claim/verify-magic-link` creates user and claims business
- [ ] Frontend form submits and advances through steps
- [ ] Magic link verification redirects to dashboard
- [ ] User has `merchant_admin` role flag
- [ ] Business `owner_id` is set correctly

---

## Security Considerations

1. **Rate Limiting**: Apply to `/start` endpoint (5 per IP per hour)
2. **Session Expiry**: Delete incomplete sessions after 24 hours
3. **Token Security**: Magic link tokens are cryptographically random (32 bytes)
4. **Phone Verification First**: Email link only works after phone verified
5. **One-Time Links**: Magic link invalidated after use

---

## Related Files

- `backend/app/services/otp_service_v2.py` - Existing OTP service
- `backend/app/routers/auth.py` - Existing auth endpoints (reference)
- `apps/merchant/src/lib/api.ts` - API client configuration

---

**End of Implementation Prompt**
