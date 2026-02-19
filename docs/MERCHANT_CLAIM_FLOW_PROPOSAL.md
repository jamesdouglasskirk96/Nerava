# Merchant Business Claim Flow: Email + Phone → Magic Link

## Overview

A streamlined merchant onboarding flow that combines:
1. **Business Claim** - Merchant provides business info
2. **Dual Verification** - Email + Phone verification
3. **Magic Link** - Passwordless authentication

## Why This Flow?

### Advantages
✅ **No Google Dependency** - Works without Google OAuth setup  
✅ **Dual Verification** - Email + Phone = stronger security  
✅ **Better UX** - Magic link is simpler than OAuth redirects  
✅ **Uses Existing Infrastructure** - OTP + Magic Link already built  
✅ **Business Verification** - Phone ensures real business owner  
✅ **Passwordless** - No password management needed  

### Current State
- ✅ Magic Link system exists (`/v1/auth/magic_link/*`)
- ✅ Phone OTP system exists (`/v1/auth/otp/*`)
- ✅ Email sending configured
- ❌ Combined flow not yet implemented

## Proposed Flow

### Step 1: Business Claim Form
**Route:** `/merchant/claim`

Merchant provides:
- Business name
- Email address
- Phone number
- (Optional) Business address/location

**UI:**
```
┌─────────────────────────────────────┐
│  Claim Your Business on Nerava      │
├─────────────────────────────────────┤
│  Business Name: [____________]     │
│  Email:        [____________]       │
│  Phone:        [____________]       │
│                                     │
│  [Continue]                         │
└─────────────────────────────────────┘
```

### Step 2: Phone Verification
**Route:** `/merchant/claim/verify-phone`

1. Send OTP to phone: `POST /v1/auth/otp/start`
2. User enters 6-digit code
3. Verify code: `POST /v1/auth/otp/verify`
4. Store verified phone number

**UI:**
```
┌─────────────────────────────────────┐
│  Verify Your Phone                  │
├─────────────────────────────────────┤
│  We sent a code to                  │
│  +1 (713) ***-6318                 │
│                                     │
│  Enter code: [__] [__] [__] [__]   │
│                                     │
│  [Verify] [Resend Code]             │
└─────────────────────────────────────┘
```

### Step 3: Email Verification + Magic Link
**Route:** `/merchant/claim/verify-email`

1. Send magic link to email: `POST /v1/auth/magic_link/request`
2. User clicks link in email
3. Link redirects to: `/merchant/auth/magic?token=...`
4. Verify token: `POST /v1/auth/magic_link/verify`
5. Create merchant user with:
   - Email (verified)
   - Phone (verified)
   - Business name
   - Role: `merchant_admin`

**UI:**
```
┌─────────────────────────────────────┐
│  Verify Your Email                  │
├─────────────────────────────────────┤
│  We sent a magic link to            │
│  merchant@example.com               │
│                                     │
│  Check your email and click the     │
│  link to complete verification.     │
│                                     │
│  [Resend Email]                     │
└─────────────────────────────────────┘
```

### Step 4: Location Selection (Optional)
**Route:** `/merchant/claim/location`

After both verifications complete, merchant can:
- Select business location
- Link Google Business Profile (optional)
- Set up billing

## Implementation Plan

### Backend: New Endpoint

**File:** `backend/app/routers/merchant_onboarding.py`

```python
@router.post("/claim/start")
async def start_merchant_claim(
    payload: MerchantClaimRequest,
    db: Session = Depends(get_db),
):
    """
    Start merchant claim flow.
    
    Steps:
    1. Validate business name, email, phone
    2. Check if email/phone already claimed
    3. Send OTP to phone
    4. Return claim session ID
    """
    # Validate inputs
    # Check for existing claims
    # Send OTP
    # Create claim session
    pass

@router.post("/claim/verify-phone")
async def verify_phone_for_claim(
    payload: PhoneVerifyRequest,
    claim_session_id: str,
    db: Session = Depends(get_db),
):
    """
    Verify phone number for claim.
    
    Uses existing OTP verification.
    Stores verified phone in claim session.
    """
    # Verify OTP using existing endpoint
    # Store verified phone in session
    pass

@router.post("/claim/verify-email")
async def send_magic_link_for_claim(
    claim_session_id: str,
    db: Session = Depends(get_db),
):
    """
    Send magic link after phone verification.
    
    Creates user with email + phone.
    Sends magic link.
    """
    # Get claim session (with verified phone)
    # Create user with email + phone
    # Send magic link
    pass
```

### Frontend: New Components

**File:** `apps/merchant/app/components/ClaimBusiness.tsx`

```typescript
export function ClaimBusiness() {
  const [step, setStep] = useState<'form' | 'phone' | 'email' | 'complete'>('form')
  const [businessName, setBusinessName] = useState('')
  const [email, setEmail] = useState('')
  const [phone, setPhone] = useState('')
  
  const handleSubmit = async () => {
    // POST /v1/merchant/claim/start
    // Move to phone verification step
  }
  
  const handlePhoneVerify = async (code: string) => {
    // POST /v1/auth/otp/verify
    // Move to email verification step
  }
  
  // Render based on step
}
```

## API Flow Diagram

```
┌─────────────┐
│   Merchant  │
│   Portal    │
└──────┬──────┘
       │
       │ 1. POST /v1/merchant/claim/start
       │    { business_name, email, phone }
       ▼
┌─────────────────────┐
│   Backend           │
│   - Validate        │
│   - Send OTP        │
│   - Create session  │
└──────┬──────────────┘
       │
       │ 2. User enters OTP code
       │    POST /v1/auth/otp/verify
       ▼
┌─────────────────────┐
│   Backend           │
│   - Verify OTP      │
│   - Store phone      │
└──────┬──────────────┘
       │
       │ 3. POST /v1/merchant/claim/verify-email
       │    (sends magic link)
       ▼
┌─────────────────────┐
│   Email Service     │
│   - Send magic link │
└──────┬──────────────┘
       │
       │ 4. User clicks link
       │    POST /v1/auth/magic_link/verify
       ▼
┌─────────────────────┐
│   Backend           │
│   - Create user     │
│   - Set role        │
│   - Return token     │
└──────┬──────────────┘
       │
       │ 5. Redirect to dashboard
       ▼
┌─────────────┐
│  Dashboard  │
└─────────────┘
```

## Database Schema

### New Table: `merchant_claim_sessions`

```sql
CREATE TABLE merchant_claim_sessions (
    id SERIAL PRIMARY KEY,
    session_id UUID UNIQUE NOT NULL,
    business_name VARCHAR(255) NOT NULL,
    email VARCHAR(255) NOT NULL,
    phone VARCHAR(20) NOT NULL,
    phone_verified BOOLEAN DEFAULT FALSE,
    email_verified BOOLEAN DEFAULT FALSE,
    user_id INTEGER REFERENCES users(id),
    expires_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT NOW()
);
```

## Security Considerations

1. **Rate Limiting**
   - Limit claim attempts per email/phone
   - Use existing OTP rate limiting

2. **Session Expiry**
   - Claim sessions expire after 1 hour
   - OTP codes expire after 10 minutes
   - Magic links expire after 15 minutes

3. **Duplicate Prevention**
   - Check if email already has merchant account
   - Check if phone already claimed
   - Prevent multiple claims for same business

4. **Audit Logging**
   - Log all claim attempts
   - Log verification steps
   - Track failed attempts

## Migration Path

### Phase 1: Backend
1. Create `merchant_claim_sessions` table
2. Add `/v1/merchant/claim/*` endpoints
3. Integrate with existing OTP + Magic Link

### Phase 2: Frontend
1. Update `ClaimBusiness.tsx` component
2. Add phone verification step
3. Add email verification step
4. Handle magic link callback

### Phase 3: Testing
1. Test full flow end-to-end
2. Test edge cases (duplicates, expired sessions)
3. Test rate limiting

## Comparison: Current vs Proposed

| Aspect | Current (Google OAuth) | Proposed (Email + Phone) |
|--------|----------------------|-------------------------|
| **Setup** | Requires Google OAuth config | Uses existing systems |
| **Verification** | Google Business Profile | Email + Phone |
| **UX** | OAuth redirect flow | In-app flow |
| **Dependencies** | Google API | Twilio + Email |
| **Security** | Single factor (Google) | Dual factor (Email + Phone) |
| **Implementation** | Complex OAuth flow | Simple API calls |

## Next Steps

1. **Review & Approve** this flow
2. **Create database migration** for `merchant_claim_sessions`
3. **Implement backend endpoints**
4. **Update frontend components**
5. **Test end-to-end**
6. **Deploy**

## Questions to Consider

1. Should phone verification be required, or optional?
2. Should we allow claiming multiple businesses with same email?
3. What happens if user already has account (driver)?
4. Should we add business address verification?
5. Do we need admin approval before activation?




