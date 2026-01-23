# Admin & Merchant Portal Feature Inventory

**Generated:** January 23, 2026
**Purpose:** Complete inventory of features in both portals

---

## ADMIN PORTAL

### Overview

**Location:** `/Users/jameskirk/Desktop/Nerava/apps/admin/`
**Tech Stack:** React, TypeScript, Vite, Tailwind CSS, Radix UI
**Status:** UI complete, mixed real/mock data

---

### Page-by-Page Feature List

#### 1. Dashboard (`/`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Active Merchants stat card | ✅ UI | 🔸 Mock (847) |
| Charging Locations stat card | ✅ UI | 🔸 Mock (1,243) |
| Live Exclusive Sessions stat card | ✅ UI | 🔸 Mock (312) |
| Alerts count badge | ✅ UI | 🔸 Mock (7) |
| Recent Alerts list | ✅ UI | 🔸 Mock data |
| Alert types: merchant_abuse, charger_data_issue, location_mismatch | ✅ UI | 🔸 Mock |
| Recent Activity feed | ✅ UI | 🔸 Mock data |
| Activity types: merchant_pause, session_extension, exclusive_toggle | ✅ UI | 🔸 Mock |

**Screenshot Description:** Dark themed dashboard with 4 stat cards at top, two-column layout below with alerts on left, activity on right.

---

#### 2. Merchants (`/merchants`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Search merchants by name | ✅ Full | ✅ Real API |
| Merchant table with columns | ✅ Full | ✅ Real API |
| - ID column | ✅ | ✅ |
| - Name column | ✅ | ✅ |
| - Zone column | ✅ | ✅ |
| - Status badges (active/paused/flagged) | ✅ | ✅ |
| - Nova Balance column | ✅ | ✅ |
| View Portal button (external link) | ✅ UI | N/A |
| Send Portal Link button | ✅ UI | ❌ No API |

**API:** `GET /v1/admin/merchants?query={search}`

---

#### 3. Charging Locations (`/charging-locations`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Location cards list | ✅ UI | 🔸 Mock |
| Location name & address | ✅ UI | 🔸 Mock |
| Associated merchants list | ✅ UI | 🔸 Mock |
| Live sessions count | ✅ UI | 🔸 Mock |
| Total chargers count | ✅ UI | 🔸 Mock |
| Primary Experience toggle | ✅ UI | 🔸 Mock (no backend) |

**Mock Locations:** Tesla Market Heights, Whole Foods - Montrose, Target - Memorial City

---

#### 4. Active Sessions (`/active-sessions`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Auto-refresh (30 sec) | ✅ Full | ✅ Real API |
| Total Active sessions stat | ✅ Full | ✅ Real API |
| Average Time Remaining stat | ✅ Full | ✅ Real API |
| Sessions table | ✅ Full | ✅ Real API |
| - Session ID | ✅ | ✅ |
| - Driver ID | ✅ | ✅ |
| - Merchant | ✅ | ✅ |
| - Charger | ✅ | ✅ |
| - Time Remaining | ✅ | ✅ |
| - Status (ACTIVE/COMPLETED/EXPIRED) | ✅ | ✅ |
| Status color coding | ✅ Full | N/A |

**API:** `GET /v1/admin/sessions/active`

---

#### 5. Exclusives (`/exclusives`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Total Exclusives stat | ✅ UI | 🔸 Mock |
| Active count stat | ✅ UI | 🔸 Mock |
| Paused count stat | ✅ UI | 🔸 Mock |
| Activations Today stat | ✅ UI | 🔸 Mock |
| Exclusives table | ✅ UI | 🔸 Mock |
| - ID column | ✅ UI | 🔸 Mock |
| - Merchant column | ✅ UI | 🔸 Mock |
| - Type column | ✅ UI | 🔸 Mock |
| - Status column | ✅ UI | 🔸 Mock |
| - Activations Today | ✅ UI | 🔸 Mock |
| - Daily Cap with progress bar | ✅ UI | 🔸 Mock |
| - Monthly Progress with progress bar | ✅ UI | 🔸 Mock |
| Edit action | ✅ UI | ❌ No API |
| Pause/Resume toggle | ✅ UI | ❌ No API |
| Disable action | ✅ UI | ❌ No API |

**Missing API:** `POST /v1/admin/exclusives/{id}/toggle`

---

#### 6. Overrides (`/overrides`) ⚠️ Critical Controls

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Warning banner (system-wide effects) | ✅ UI | N/A |
| Force-Close All Sessions at Location | ✅ UI | ❌ No API |
| - Location dropdown | ✅ UI | 🔸 Mock locations |
| - Confirm dialog | ✅ UI | N/A |
| Disable Primary Experience | ✅ UI | ❌ No API |
| - Location dropdown | ✅ UI | 🔸 Mock |
| Reset Caps | ✅ UI | ❌ No API |
| - Location dropdown | ✅ UI | 🔸 Mock |
| - Cap type selector | ✅ UI | N/A |
| Emergency Pause (system-wide) | ✅ UI | ❌ No API |
| Recent Overrides Log | ✅ UI | 🔸 Mock |

**Severity Levels:** Critical (force-close, disable, emergency), Medium (reset caps)

---

#### 7. Logs (`/logs`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Search logs | ✅ UI | 🔸 Mock |
| Filter by log type | ✅ UI | 🔸 Mock |
| - admin, error, system, user, merchant | ✅ UI | 🔸 Mock |
| Log stats by type | ✅ UI | 🔸 Mock |
| Logs table | ✅ UI | 🔸 Mock |
| - Timestamp column | ✅ UI | 🔸 Mock |
| - Type column with badges | ✅ UI | 🔸 Mock |
| - Action column | ✅ UI | 🔸 Mock |
| - Details column | ✅ UI | 🔸 Mock |
| - Operator column | ✅ UI | 🔸 Mock |
| - IP Address column | ✅ UI | 🔸 Mock |
| Export button | ✅ UI | ❌ Not implemented |

**Missing API:** `GET /v1/admin/logs?type={type}&search={search}`

---

#### 8. Sidebar Navigation

| Feature | Implementation |
|---------|---------------|
| Dashboard link | ✅ |
| Merchants link | ✅ |
| Charging Locations link | ✅ |
| Active Sessions link | ✅ |
| Exclusives link | ✅ |
| Overrides link | ✅ |
| Logs link | ✅ |
| Operator email display | ✅ |
| Session date display | ✅ |

---

### Secondary Admin App (`/ui-admin/`)

**Location:** `/Users/jameskirk/Desktop/Nerava/ui-admin/`
**Status:** Simpler, but fully API-connected

| Page | Features | Data Source |
|------|----------|-------------|
| Users (`/users`) | Search, list, wallet view, wallet adjust | ✅ Real API |
| Merchants (`/merchants`) | Search, list, detail view | ✅ Real API |
| Locations (`/locations`) | Google Places search, candidate selection, resolve | ✅ Real API |

---

## MERCHANT PORTAL

### Overview

**Location:** `/Users/jameskirk/Desktop/Nerava/apps/merchant/`
**Tech Stack:** React, TypeScript, Vite, Tailwind CSS
**Status:** Onboarding flow + dashboard, mixed real/mock

---

### Onboarding Flow

#### Claim Business (`/claim`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Google Business Profile OAuth button | ✅ UI | 🔸 Partial backend |
| OAuth redirect handling | ✅ UI | 🔸 Partial |
| Error state handling | ✅ UI | N/A |

#### Select Location (`/claim/location`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| List of Google locations | ✅ UI | 🔸 Partial API |
| Location selection | ✅ UI | 🔸 Partial |
| Claim confirmation | ✅ UI | 🔸 Partial |

---

### Dashboard Pages (Requires `isClaimed` state)

#### Overview (`/overview`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| KPI cards | ✅ UI | ✅ Real API (with mock fallback) |
| - Verified Sessions | ✅ | ✅ |
| - Purchase Rewards | ✅ | ✅ |
| - Total Rewards Paid | ✅ | ✅ |
| Top Hours chart | ✅ UI | ✅ Real API |
| Recent Events list | ✅ UI | ✅ Real API |

**API:** `GET /v1/merchant/summary`

---

#### Exclusives (`/exclusives`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| List all exclusives | ✅ Full | ✅ Real API |
| Exclusive card display | ✅ Full | ✅ |
| - Title & description | ✅ | ✅ |
| - Nova reward amount | ✅ | ✅ |
| - Active status toggle | ✅ | ✅ Real API |
| Create new exclusive button | ✅ UI | Links to /exclusives/new |

**API:** `GET /v1/merchants/{id}/exclusives`

---

#### Create Exclusive (`/exclusives/new`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Title input | ✅ Full | N/A |
| Description textarea | ✅ Full | N/A |
| Nova reward amount | ✅ Full | N/A |
| Submit button | ✅ Full | ✅ Real API |
| Validation | ✅ Full | N/A |

**API:** `POST /v1/merchants/{id}/exclusives`

---

#### Visits (`/visits`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Visit history list | ✅ UI | 🔸 Partial API |
| - Driver info | ✅ UI | 🔸 |
| - Visit duration | ✅ UI | 🔸 |
| - Timestamp | ✅ UI | 🔸 |
| - Status | ✅ UI | 🔸 |

---

#### Primary Experience (`/primary-experience`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Enable/disable toggle | ✅ UI | 🔸 Mock (no backend) |
| Configuration options | ✅ UI | 🔸 Mock |
| Status display | ✅ UI | 🔸 Mock |

**Status:** UI only, backend not implemented

---

#### Pickup Packages (`/pickup-packages`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Package list | ✅ UI | 🔸 Partial |
| Package cards | ✅ UI | 🔸 |
| Create new link | ✅ UI | Links to /pickup-packages/new |

#### Create Pickup Package (`/pickup-packages/new`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Package name input | ✅ UI | N/A |
| Description | ✅ UI | N/A |
| Price input | ✅ UI | N/A |
| Submit | ✅ UI | 🔸 Partial API |

---

#### Billing (`/billing`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Current balance display | ✅ UI | 🔸 Mock |
| Billing history table | ✅ UI | 🔸 Mock |
| Payment method display | ✅ UI | 🔸 Mock |
| Add payment method | ✅ UI | 🔸 Partial (SetupIntent exists) |

**Status:** Shows mock data, no real Stripe charges

---

#### Settings (`/settings`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Business name | ✅ UI | 🔸 Hardcoded |
| Business address | ✅ UI | 🔸 Hardcoded |
| Contact email | ✅ UI | 🔸 Hardcoded |
| Contact phone | ✅ UI | 🔸 Hardcoded |
| Hours of operation | ✅ UI | 🔸 Hardcoded |
| Save button | ✅ UI | ❌ No API |

**Status:** All data hardcoded, save does nothing

---

#### Customer Exclusive View (`/exclusive/:exclusiveId`)

| Feature | Implementation | Data Source |
|---------|---------------|-------------|
| Exclusive details display | ✅ UI | ✅ Real API |
| Staff instructions | ✅ UI | 🔸 Partial |
| QR code (if applicable) | ✅ UI | 🔸 Partial |

**Purpose:** Staff-facing view when customer redeems exclusive

---

### Shared Components

| Component | Location | Purpose |
|-----------|----------|---------|
| BrandImageUpload.tsx | `/components/` | Upload merchant brand image |
| Sidebar/Navigation | `/components/` | Dashboard navigation |
| API Service | `/services/api.ts` | API client with auth |

---

## Feature Summary Matrix

### Admin Portal

| Feature | UI | API | Production Ready |
|---------|-----|-----|------------------|
| Dashboard Stats | ✅ | ❌ Mock | ❌ |
| Dashboard Alerts | ✅ | ❌ Mock | ❌ |
| Merchant Search | ✅ | ✅ | ✅ |
| Merchant Actions | ✅ | ❌ | ❌ |
| Charging Locations | ✅ | ❌ Mock | ❌ |
| Active Sessions | ✅ | ✅ | ✅ |
| Exclusives Management | ✅ | ❌ Mock | ❌ |
| Override Controls | ✅ | ❌ | ❌ |
| Audit Logs | ✅ | ❌ Mock | ❌ |
| User Wallet Management | ✅ | ✅ | ✅ |
| Google Places Mapping | ✅ | ✅ | ✅ |
| Nova Grants | ✅ | ✅ | ✅ |

### Merchant Portal

| Feature | UI | API | Production Ready |
|---------|-----|-----|------------------|
| Google OAuth Onboarding | ✅ | 🔸 Partial | ❌ |
| Location Claiming | ✅ | 🔸 Partial | ❌ |
| Overview Dashboard | ✅ | ✅ | ✅ |
| Exclusive CRUD | ✅ | ✅ | ✅ |
| Exclusive Toggle | ✅ | ✅ | ✅ |
| Visit History | ✅ | 🔸 Partial | ❌ |
| Primary Experience | ✅ | ❌ | ❌ |
| Pickup Packages | ✅ | 🔸 Partial | ❌ |
| Billing | ✅ | ❌ Mock | ❌ |
| Settings | ✅ | ❌ | ❌ |
| Brand Image Upload | ✅ | ✅ | ✅ |

---

## Legend

- ✅ = Fully implemented
- 🔸 = Partially implemented
- ❌ = Not implemented / Mock only
