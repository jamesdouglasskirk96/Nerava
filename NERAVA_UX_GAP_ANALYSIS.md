# Nerava UX Gap Analysis & PlugShare Feature Parity Report

**Date:** March 2, 2026
**Scope:** Comprehensive audit of Nerava driver app UX, backend capabilities, and feature gaps relative to PlugShare
**Methodology:** Full codebase exploration (408 backend endpoints, 25+ frontend screens, 35+ DB tables), PlugShare feature research (help docs, user reviews, competitive analyses), and cross-referencing against the existing PLUGSHARE_COMPETITIVE_ANALYSIS.md

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Critical Gap: Account Identity](#2-critical-gap-account-identity)
3. [Discovery & Map UX Gaps](#3-discovery--map-ux-gaps)
4. [Charger Detail & Information Gaps](#4-charger-detail--information-gaps)
5. [Post-Session & Community Gaps](#5-post-session--community-gaps)
6. [Driver Profile & Personalization Gaps](#6-driver-profile--personalization-gaps)
7. [Navigation & Trip Planning Gaps](#7-navigation--trip-planning-gaps)
8. [Notifications & Engagement Gaps](#8-notifications--engagement-gaps)
9. [Payment & Pricing Gaps](#9-payment--pricing-gaps)
10. [Data Quality & Freshness Gaps](#10-data-quality--freshness-gaps)
11. [Mobile Platform & Performance Gaps](#11-mobile-platform--performance-gaps)
12. [PlugShare Feature Parity Matrix](#12-plugshare-feature-parity-matrix)
13. [What NOT to Build](#13-what-not-to-build)
14. [Prioritized Roadmap](#14-prioritized-roadmap)
15. [Appendix: Backend Capability Inventory](#15-appendix-backend-capability-inventory)

---

## 1. Executive Summary

Nerava has a strong foundation for **incentivized charging** (campaigns, wallets, reputation tiers, Tesla API integration) but significant gaps in **charger discovery UX** — the thing drivers do before they ever earn a reward. A driver who can't find, evaluate, and navigate to the right charger will never reach the reward layer.

### Where Nerava Excels (vs. PlugShare)
| Capability | Nerava | PlugShare |
|-----------|--------|-----------|
| Verified charging sessions | Tesla Fleet API + quality_score anti-fraud | Manual check-in (self-reported) |
| Financial rewards | Nova points + cash via Stripe Express | None |
| Merchant integration | Exclusive offers, walk-time, dwell verification | "Amenities" tags only (no business relationship) |
| Campaign targeting | 15+ rule dimensions, priority-weighted matching | None |
| Reputation system | Bronze → Platinum tiers, streak tracking | PlugScore (charger-level, not driver-level) |
| Energy data | kWh, power_kw, battery %, charge rate per session | None (no vehicle API) |

### Where PlugShare Excels (vs. Nerava)
| Capability | PlugShare | Nerava |
|-----------|-----------|--------|
| Station count | 750K+ stations, 200+ countries | ~20 chargers (NREL seed, 8+ stall filter) |
| User reviews | 6.5M+ check-ins with text, photos, ratings | Zero reviews system |
| Real-time availability | Network-fed status (partial) + crowd-sourced check-ins | Charger `status` field (stale, no real-time feed) |
| Connector filtering | J1772, CCS, CHAdeMO, NACS with per-vehicle auto-filter | No connector filter in UI |
| Trip planning | Route planner with range radius, elevation, waypoints | None |
| Pricing display | Per-kWh and session fees (inconsistent but present) | None |
| Vehicle profiles | Up to 4 vehicles with auto-filter | Single Tesla connection, no connector prefs |
| Community photos | 725K+ user-uploaded station photos | Google Places photos only |
| Offline capability | None (gap for both) | None |
| Driver profiles | Public profile with check-in history, vehicle, reviews | User ID 17: null email, null phone, null display_name |

### The Core Problem

**Nerava is building from the reward layer down. It needs to build from the discovery layer up.**

A driver opens Nerava today and sees: a map with blue pins, a search bar, filter pills, and a bottom sheet with charger cards. They cannot:
- See how many stalls are available right now
- Read what other drivers experienced at a charger
- Filter by connector type or power level
- See what it costs to charge there
- Plan a route with charging stops
- Upload a photo of a broken connector
- Know if the charger even works

Until these basics are solved, the reward layer (which is excellent) has no funnel feeding it.

---

## 2. Critical Gap: Account Identity

### Current State
User ID 17 (the only production user) has:
```json
{
  "email": null,
  "phone": null,
  "display_name": null,
  "auth_provider": "tesla",
  "avatar_url": null,
  "vehicle_color": null,
  "vehicle_model": null
}
```

Tesla OAuth creates a user record with a `tesla_user_id` UUID but stores **no contact information**. The Tesla Fleet API does not expose the user's email address.

### What This Breaks

| Feature | Why It Needs Identity |
|---------|----------------------|
| Campaign allowlists | Sponsors whitelist by email — impossible if email is null |
| Stripe payouts | Stripe Connect Express requires email for account creation |
| Account recovery | If Tesla token expires and refresh fails, user is permanently locked out |
| Push notifications (email) | No fallback channel if APNs token expires |
| Session receipts | Can't email charging summaries or earnings reports |
| Merchant verification | "Show this to staff" codes need a name/photo for trust |
| Community features | Reviews, profiles, social — all need a display identity |
| Driver-to-driver messaging | PlugShare has DMs; Nerava can't even name the user |
| Terms of Service acceptance | Legal compliance requires a contact method |
| Fraud investigation | No way to contact a user suspected of abuse |

### Recommendation

**Post-Tesla-OAuth profile completion flow:**

1. After Tesla OAuth succeeds → show "Complete Your Profile" screen
2. Required: email (validated format, confirmation email sent)
3. Optional: display name, phone, vehicle color/model
4. Skip-able but with persistent banner: "Complete your profile to earn rewards"
5. **Gate payouts on email** — Stripe needs it anyway
6. **Gate campaign eligibility on email** — IncentiveEngine skips null-email users for allowlist campaigns
7. Store Tesla VIN-derived vehicle model automatically (we already have `vin: 7SAYGDEF3NF394382` → decode to "Model Y Long Range")

### Backend Impact
- `users` table already has `email`, `phone`, `display_name`, `avatar_url`, `vehicle_color`, `vehicle_model` columns
- Need new endpoint: `POST /v1/auth/complete-profile` (accepts email, display_name, phone, vehicle prefs)
- Need email verification flow (magic link or code)
- Update `IncentiveEngine` to check `users.email IS NOT NULL` for allowlist campaigns

### Frontend Impact
- New `ProfileCompletionScreen` component after Tesla OAuth callback
- Persistent `CompleteProfileBanner` in DriverHome when email is null
- Account page shows "Email: Not set — Add email" prompt
- Gate "Withdraw to Bank" button on email completion

**Effort:** 8-12 hours (backend + frontend + email verification)
**Priority:** P0 — blocks campaign targeting, payouts, and account recovery

---

## 3. Discovery & Map UX Gaps

<!-- ### 3.1 Map Tile Quality

**Current:** OpenStreetMap tiles (`https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png`)
**PlugShare:** Uses Mapbox with satellite/hybrid toggle
**Gap:** OSM tiles are functional but visually inferior to Mapbox/Google Maps. No satellite or terrain view.

**Recommendation:** Switch to Mapbox GL JS for vector tiles (better zoom performance, 3D buildings, satellite toggle). Free tier: 50K map loads/month. Or use Google Maps Platform (already have API key for Places).

**Effort:** 6-8 hours | **Priority:** P2 -->

### 3.2 Charger Pin Information

**Current:** Blue circle with ⚡ emoji (32px). Selected: 40px with pulse. No information on the pin itself.
**PlugShare:** Color-coded pins (green=L2, orange=DCFC, blue=residential, brown=restricted, wrench=broken). Power level visible without tapping.

**Gap:** All chargers look identical. A 350kW Supercharger and a 7kW Level 2 destination charger have the same pin. Driver can't visually scan the map to find fast chargers.

**Recommendation:**
- Color-code by power level: Green (≤20kW L2), Blue (20-100kW), Orange (100-250kW), Red (250kW+)
- Show power level on pin: "150kW" text below icon for zoomed-in view
- Different icon shape: Circle for L2, Lightning bolt for DCFC
- Gray/dimmed for broken or offline chargers
- Show stall count on pin when zoomed in: "12" inside the circle

**Effort:** 4-6 hours | **Priority:** P1

### 3.3 Connector Type Filtering

**Current:** Filter pills are amenity-based only (Bathroom, Food, WiFi, Pets, Music). No way to filter by connector type.
**PlugShare:** Filter by J1772, CCS, CHAdeMO, Tesla/NACS, wall outlets. Auto-filters based on vehicle profile.

**Gap:** A non-Tesla driver (future Smartcar integration) seeing Tesla Superchargers they can't use. Even Tesla drivers may want to filter by Supercharger vs. Destination charger.

**Recommendation:**
- Add filter row: "Tesla SC", "CCS", "CHAdeMO", "Level 2", "DC Fast"
- Auto-select compatible connectors based on vehicle profile (Tesla → show Tesla SC + CCS)
- Backend already has `connector_types` JSON column on chargers table — just needs UI

**Data available:** `chargers.connector_types` (JSON array), `chargers.power_kw`, `chargers.network_name`
**Effort:** 4-6 hours | **Priority:** P1

### 3.4 Power Level Filtering

**Current:** Only filter is 8+ stalls (hardcoded in DiscoveryView.tsx line 54: `if (c.num_evse != null && c.num_evse < 8) return false`).
**PlugShare:** Minimum kW slider (50kW, 100kW, 150kW+).

**Gap:** The 8+ stalls filter is a blunt instrument. It removes all Level 2 chargers and small DCFC sites. A driver at a hotel with a 4-stall destination charger would see nothing.

**Recommendation:**
- Replace hardcoded 8-stall filter with user-selectable power/stall preferences
- Add "DC Fast Only" quick filter toggle
- Add minimum power slider in advanced filters
- Remember user's filter preferences (localStorage)

**Effort:** 3-4 hours | **Priority:** P1

### 3.5 Network Filtering

**Current:** No way to filter by charging network.
**PlugShare:** Filter by ChargePoint, Tesla, Electrify America, EVgo, etc.

**Gap:** Drivers with specific network memberships (ChargePoint, EVgo) can't filter to their networks.

**Recommendation:**
- Add network filter in advanced filters panel
- Show top 5 networks present in current map view as quick toggles
- Backend already has `chargers.network_name`

**Effort:** 2-3 hours | **Priority:** P2

<!-- ### 3.6 Search Functionality

**Current:** Search bar filters the existing card list by name/network. Does not search for locations, addresses, or POIs.
**PlugShare:** Full location search (addresses, cities, POIs) + station name search.

**Gap:** Driver can't type "Austin Airport" and see chargers near there. Can only search within currently loaded chargers.

**Recommendation:**
- Integrate geocoding (Google Geocoding API or Mapbox) for address/POI search
- When user searches for a location → pan map to that location → reload chargers
- Keep current name-filter behavior for charger-specific queries

**Effort:** 6-8 hours | **Priority:** P1 -->

### 3.7 Map Clustering

**Current:** All pins rendered individually. At zoom level 10 with 20 chargers, pins overlap.
**PlugShare:** Clusters pins at low zoom levels, shows count badges.

**Gap:** When map shows a wide area (e.g., all of Austin metro), pins stack on top of each other making them untappable.

**Recommendation:**
- Add Leaflet.markercluster plugin (or Mapbox clustering if switching tiles)
- Cluster at zoom ≤12, show individual pins at zoom ≥13
- Cluster badge shows count: "5 chargers"

**Effort:** 2-3 hours | **Priority:** P2

<!-- ### 3.8 Bottom Sheet UX

**Current:** Three snap points (peek=160px, half=55vh, full=92vh). Drag handle works but no momentum/velocity-based snapping.
**PlugShare:** Smooth spring-physics bottom sheet with rubber-band effect.

**Gap:** Current sheet feels mechanical. No velocity-based snapping (a fast swipe should go further than a slow drag). No rubber-band at boundaries.

**Recommendation:**
- Add velocity tracking to touch handlers (dy/dt at touchend)
- Fast swipe up → jump to full. Fast swipe down → jump to peek.
- Add rubber-band effect at peek (slight overscroll bounce)
- Consider using `framer-motion` or `react-spring` for physics-based animation

**Effort:** 4-6 hours | **Priority:** P3 -->

---

## 4. Charger Detail & Information Gaps

### 4.1 No Charger Detail Screen

**Current:** Tapping a charger card in DiscoveryView calls `onChargerSelect` which opens a full-screen modal showing the charger name + nearby merchants. It's essentially a "merchants at this charger" view, not a charger detail view.
**PlugShare:** Tapping a station opens a rich detail page: hero photo, PlugScore, specs, amenities, pricing, reviews, photos, check-in history.

**Gap:** This is the single largest UX gap. Drivers cannot learn anything about a charger before deciding to drive there.

**Recommendation:** Build a dedicated ChargerDetailScreen with:
- Hero image (network logo or street view as fallback)
- **Nerava Score** (see §4.2)
- Specs: connector types, power kW, number of stalls, network
- Amenities: restrooms, food, WiFi (from nearby merchant data)
- Pricing: per-kWh cost (from NREL data, see §9)
- Net cost after Nerava rewards (unique differentiator)
- Nearby merchants carousel (existing functionality, moved here)
- Recent sessions: "12 Nerava drivers charged here this week"
- Reviews section (see §5.1)
- "Get Directions" CTA
- "Start Charging" CTA (when at charger)

**Backend:** Most data already exists in `chargers` table. Need new endpoint: `GET /v1/chargers/{charger_id}/detail` returning enriched data.
**Effort:** 12-16 hours | **Priority:** P0

### 4.2 No Charger Reliability Score

**Current:** No scoring system for chargers.
**PlugShare:** PlugScore (1-10) based on recent check-ins. Known to be gamed by EVgo (PlugShare's owner).

**Gap:** Drivers have no way to assess charger reliability before visiting.

**Recommendation:** Build "Nerava Score" (1-10):
- 30% session completion rate (sessions that end normally vs. error/timeout)
- 20% average quality_score from SessionEvent
- 15% kWh delivery consistency (actual vs. rated power)
- 25% community rating (from reviews, once built)
- 10% recency weight (recent data matters more)

**Advantage over PlugScore:** Nerava Score is based on **verified Tesla API data**, not self-reported check-ins. Can't be gamed. This is a significant competitive differentiator.

**Backend:** Can compute from existing `session_events` table. Need materialized view or periodic job.
**Effort:** 6-8 hours | **Priority:** P1

### 4.3 No Amenity Information

**Current:** Amenity filter pills exist (Bathroom, Food, WiFi, Pets, Music) but they filter merchants, not chargers. No amenity data displayed for chargers themselves.
**PlugShare:** 14 amenity categories per station (Lodging, Dining, Restrooms, Shopping, Park, Grocery, WiFi, Valet, Hiking, Camping, Free Charging, Covered Parking, Illuminated, Garage).

**Gap:** Driver can't see if a charger has restrooms, covered parking, or is well-lit at night.

**Recommendation:**
- Derive charger amenities from nearby merchants (already linked via `charger_merchants` table)
- Add charger-level amenity fields: `has_restrooms`, `is_covered`, `is_illuminated`, `has_food_nearby`, `parking_type`
- Allow community voting on charger amenities (extend existing `amenity_vote` model)
- Display as icon row on charger detail screen

**Effort:** 4-6 hours | **Priority:** P2

### 4.4 No Real-Time Availability

**Current:** `chargers.status` field exists (available/in_use/broken/unknown) but is never updated in real-time. Set at seed time and stale.
**PlugShare:** Network-fed availability (ChargePoint, EVgo, Blink) + crowd-sourced "Charging Now" check-ins.

**Gap:** Driver drives 20 minutes to a charger only to find all stalls occupied. This is the #1 pain point for EV drivers.

**Recommendation (phased):**
- **Phase 1 (3-4 hours):** Show Nerava users currently charging at each station. Backend already tracks active sessions via `session_events`. Add to charger detail: "2 Nerava drivers charging now" with anonymous session data.
- **Phase 2 (15-20 hours):** OCPI (Open Charge Point Interface) integration for real-time status from networks. Start with ChargePoint (largest network with OCPI support).

**Priority:** Phase 1: P1, Phase 2: P2

### 4.5 No Charger Photos

**Current:** Charger cards show network logo icons (Tesla T, ChargePoint bolt). No actual photos of the charging location.
**PlugShare:** 725K+ user-uploaded photos showing stall layout, connector condition, parking, signage.

**Gap:** Photos are critical for first-time visits. "Is it behind the building?", "Is the parking lot sketchy at night?", "Which connectors are CCS vs CHAdeMO?"

**Recommendation:**
- **Phase 1:** Use Google Street View Static API to auto-generate a street-level preview for each charger (free tier: 28K loads/month). Display as hero image on charger detail.
- **Phase 2:** Allow post-session photo uploads tied to `session_event_id` (verified provenance — driver actually charged there).

**Effort:** Phase 1: 3-4 hours, Phase 2: 8-10 hours | **Priority:** Phase 1: P1, Phase 2: P2

---

## 5. Post-Session & Community Gaps

### 5.1 No Review System

**Current:** Zero review capability. No database table for reviews.
**PlugShare:** 6.5M+ reviews with text, star ratings, photos, and "helpful" votes.

**Gap:** Without reviews, charger discovery is blind. Reviews are the #1 feature users cite for choosing PlugShare over alternatives.

**Recommendation:** Build post-session review flow:
1. After session ends (detected by polling) → prompt: "How was your charge at [charger]?"
2. Star rating (1-5)
3. Quick tags: "Fast", "Reliable", "Easy Access", "Well Maintained", "Good Location" / "Slow", "Broken Stall", "Hard to Find", "Blocked by ICE", "Expensive"
4. Optional free-text comment (280 char limit)
5. Optional photo upload
6. Tied to `session_event_id` for verified provenance (only people who actually charged can review)

**Advantage over PlugShare:** Every Nerava review is linked to a verified charging session. No fake reviews, no gaming. This is a **massive trust differentiator**.

**Backend needs:**
```sql
CREATE TABLE charger_reviews (
  id UUID PRIMARY KEY,
  charger_id VARCHAR REFERENCES chargers(id),
  session_event_id UUID REFERENCES session_events(id) UNIQUE, -- one review per session
  user_id INTEGER REFERENCES users(id),
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  tags TEXT[], -- ['fast', 'reliable', 'easy_access']
  comment TEXT,
  photo_urls TEXT[], -- S3 URLs
  helpful_count INTEGER DEFAULT 0,
  created_at TIMESTAMP DEFAULT NOW()
);
```

**Effort:** 10-14 hours (backend model + API + frontend prompt + display on charger detail)
**Priority:** P0

### 5.2 No Community Activity Feed

**Current:** Backend has `/v1/social/feed` endpoint and `reward_events` table, but the frontend doesn't render any community feed.
**PlugShare:** Check-in feed per station showing recent activity.

**Gap:** No sense of community. Charging feels solitary. No "12 drivers charged here today" social proof.

**Recommendation:**
- Charger detail screen: "Recent Activity" section showing anonymized session data ("A Tesla driver charged 45 min ago, earned $2.50")
- Home screen: Optional "Nearby Activity" card showing aggregate ("3 drivers charging within 5 miles")
- Don't show individual user activity (privacy) — show aggregates only

**Effort:** 4-6 hours | **Priority:** P2

### 5.3 No "Helpful" or Report Mechanism

**Current:** No way to flag incorrect charger data.
**PlugShare:** Users can report stations as offline, under repair, permanently closed. Editorial team reviews reports.

**Gap:** If a charger is permanently closed, Nerava will keep showing it until an admin manually updates the database.

**Recommendation:**
- Add "Report Issue" button on charger detail: "Broken", "Permanently Closed", "Wrong Location", "ICE'd" (blocked by gas car)
- After N reports, auto-flag for admin review
- Show warning badge on charger: "Reported issues — check before visiting"

**Effort:** 4-6 hours | **Priority:** P2

---

## 6. Driver Profile & Personalization Gaps

### 6.1 Incomplete Account Page

**Current:** AccountPage.tsx shows: profile card (name, email, vehicle, member since), favorites, notification toggle, distance unit, Tesla status, share, logout. But for user 17: name=null, email=null, vehicle=null.

**Gap:** Account page is a skeleton. No meaningful personalization.

**Recommendation:**
- Profile header: avatar (initials-based if no photo), display name, vehicle model (decoded from VIN), member since, tier badge
- Stats row: total sessions, total kWh, total earned, reviews written
- Vehicle section: show decoded VIN info (Model Y, 2022, Long Range), connector compatibility
- Preferences: preferred charging networks, home location (for "chargers near home" feature), commute route
- Achievement badges: "First Charge", "10 Sessions", "Gold Tier", "First Review"

**Effort:** 6-8 hours | **Priority:** P1

### 6.2 No Vehicle Profile System

**Current:** Tesla connection stores `vehicle_id`, `vin`, `vehicle_name`, `vehicle_model` ("Tesla" — not decoded). Users table has `vehicle_color`, `vehicle_model` — both null.
**PlugShare:** Up to 4 vehicles per account with per-vehicle connector auto-filtering.

**Gap:** Nerava doesn't decode the VIN to get actual model/year. Doesn't use vehicle info for connector filtering. Doesn't support multiple vehicles.

**Recommendation:**
- Decode VIN on Tesla OAuth callback: `7SAYGDEF3NF394382` → Model Y, 2022, Long Range, AWD
- Auto-populate `users.vehicle_model` and show in profile
- Use vehicle model to auto-set connector compatibility (Tesla NACS + CCS via adapter)
- Future: support Smartcar for non-Tesla vehicles

**Backend:** VIN decoding is ~20 lines of Python (positions 1-3 = manufacturer, 4 = model, 10 = year). Or use NHTSA VIN API (free).
**Effort:** 3-4 hours | **Priority:** P1

### 6.3 No Favorites/Bookmarks for Chargers

**Current:** Can favorite merchants (heart icon, stored in `FavoritesContext` → localStorage + backend `favorite_merchants` table). Cannot favorite/bookmark chargers.
**PlugShare:** Bookmark any station for quick access. Saved stations show in Trip Planner.

**Gap:** Driver who charges regularly at the same Supercharger can't pin it for quick access.

**Recommendation:**
- Add heart/bookmark icon to charger cards and charger detail
- New backend table `favorite_chargers` (user_id, charger_id, created_at)
- Show favorited chargers as special pins on map (star overlay)
- "My Chargers" section in Account page
- Future: notify when new campaigns activate at favorited chargers

**Effort:** 4-6 hours | **Priority:** P1

### 6.4 No Charging Statistics Dashboard

**Current:** SessionActivityScreen shows: total sessions count, total kWh, total earned. Basic stats row.
**PlugShare:** No session analytics (PlugShare doesn't track sessions — Nerava advantage).

**Gap:** Nerava has rich session data but barely displays it. This is a **missed opportunity to differentiate**.

**Recommendation:** Build "My Charging" dashboard:
- Monthly summary: sessions, kWh, $ earned, $ saved, CO₂ offset
- Chart: charging history over time (bar chart, kWh per week)
- Breakdown by charger network (pie chart)
- Average session: duration, kWh, cost, reward
- Personal records: longest session, most kWh, highest reward
- Comparison: "You charged 40% more efficiently than average Nerava drivers"

**Effort:** 8-12 hours | **Priority:** P2 (but high differentiation value)

---

## 7. Navigation & Trip Planning Gaps

### 7.1 Directions Integration

**Current:** "Get Directions" button opens Google Maps with merchant name as destination. Uses `encodeURIComponent(merchant.name)` — may not resolve to correct location.
**PlugShare:** Direct deep-link to Apple Maps, Google Maps, or Waze with exact lat/lng coordinates.

**Gap:** Using merchant name as search query instead of coordinates can navigate to the wrong location (e.g., a different branch of the same chain).

**Recommendation:**
- Use lat/lng coordinates in directions URL: `https://www.google.com/maps/dir/?api=1&destination=${lat},${lng}`
- Detect platform: iOS → Apple Maps, Android → Google Maps
- Add Waze option
- Include charger name in label parameter

**Effort:** 1-2 hours | **Priority:** P0 (bug fix level)

### 7.2 No Trip Planner

**Current:** None.
**PlugShare:** Route planner with start/destination, vehicle range, charging stops, elevation, waypoints.
**ABRP:** More sophisticated but no merchant integration.

**Gap:** Long-distance EV travel requires charging stop planning. No solution exists that combines route planning with merchant rewards.

**Recommendation (future — high effort):**
- MVP: Enter origin/destination → show chargers along route (OSRM or Google Directions API for routing) → show merchants at each charger stop
- "Nerava twist": highlight chargers with active campaigns ("Earn $2.50 if you stop here")
- Use vehicle range from VIN-decoded model to estimate charging needs
- This is a Phase 4 feature but the **merchant rewards at each stop** is a unique differentiator no competitor has

**Effort:** 25-35 hours | **Priority:** P3 (high value but high effort)

---

## 8. Notifications & Engagement Gaps

### 8.1 No Charger Alerts

**Current:** Backend has `/v1/notifications` endpoints and `device_tokens` table. APNs integration exists in iOS shell. But no charger-specific alerts are sent.
**PlugShare:** Alerts for: station offline, station available, all plugs in use, new reviews, new nearby stations.

**Gap:** Driver has no way to be notified when a campaign starts at their favorite charger, or when a broken charger comes back online.

**Recommendation:**
- "Watch" button on charger detail → subscribe to alerts for that charger
- Alert types: new campaign at charger, charger reported broken, charger back online
- Weekly digest: "You passed 3 chargers with active rewards this week"

**Effort:** 6-8 hours | **Priority:** P2

### 8.2 No Session Receipts

**Current:** Session data is displayed in SessionActivityScreen but never sent as email/push summary.
**PlugShare:** No session receipts (no session tracking).

**Gap:** Drivers who charge for business purposes need receipts. Even casual drivers appreciate summaries.

**Recommendation:**
- After each session ends: push notification with summary ("45 min at Tesla Round Rock, 32.5 kWh, earned $2.50")
- Weekly email digest: total sessions, kWh, earnings, tier progress
- Requires email (ties back to §2 — profile completion)

**Effort:** 4-6 hours (backend + email template) | **Priority:** P2

### 8.3 No Onboarding Engagement Loop

**Current:** Onboarding is a single "Enable Location" permission screen. After that, the app dumps the user into the map.
**PlugShare:** Basic onboarding (add vehicle, set plug filters).

**Gap:** New user lands on map with no context. Doesn't understand: what is Nerava, how do rewards work, what should I tap first.

**Recommendation:**
- After first login: 3-screen onboarding carousel
  1. "Find chargers near you" (map preview)
  2. "Earn rewards while you charge" (wallet preview)
  3. "Discover nearby places" (merchant carousel preview)
- First-session tooltip: "Tap a charger to see details and nearby deals"
- Progressive disclosure: don't show wallet/earnings until first session completes

**Effort:** 4-6 hours | **Priority:** P2

---

## 9. Payment & Pricing Gaps

### 9.1 No Charging Cost Display

**Current:** No pricing data anywhere. Charger cards show distance only.
**PlugShare:** Shows pricing per station (inconsistent format but present). Data from NREL AFDC.

**Gap:** Cost is one of the top 3 factors in charger selection (along with speed and availability). Drivers can't compare costs.

**Recommendation:**
- Ingest pricing data from NREL AFDC API (already integrated for charger seeding)
- Display on charger detail: "~$0.31/kWh" or "Free" or "Pricing varies"
- **Nerava differentiator:** Show net cost after rewards: "Cost: $0.31/kWh → Net: $0.19/kWh with Nerava reward"
- This "net cost" display is unique to Nerava and directly shows value proposition

**Backend:** NREL AFDC has `ev_pricing` field. Need to store in `chargers` table or separate `charger_pricing` table.
**Effort:** 4-6 hours | **Priority:** P1

### 9.2 No Cost Tracking Per Session

**Current:** Sessions track kWh delivered and incentive earned, but not the actual cost paid to the charger network.
**PlugShare:** No cost tracking.

**Gap:** Driver can't see "I paid $12.40 to charge but earned $2.50 back via Nerava" — the ROI story isn't visible.

**Recommendation:**
- Estimate session cost: `kWh_delivered × per_kWh_rate` using charger pricing data
- Display on session card: "Estimated cost: $12.40 | Nerava reward: $2.50 | Net: $9.90"
- Monthly summary: "You saved $XX.XX with Nerava this month"

**Effort:** 3-4 hours | **Priority:** P2

---

## 10. Data Quality & Freshness Gaps

### 10.1 Stale Charger Data

**Current:** Chargers seeded from NREL once via `seed_chargers_bulk.py`. `num_evse` backfilled with heuristics (Tesla=12, ChargePoint=2). No ongoing sync.
**PlugShare:** Combination of NREL seed + network partnerships + user contributions for continuous updates.

**Gap:** New chargers installed after seed date are invisible. Closed chargers remain listed. Stall counts may be wrong.

**Recommendation:**
- Weekly NREL AFDC re-sync job (cron or scheduled Lambda)
- Tesla Supercharger API for real-time Tesla stall data
- Flag chargers not verified by any Nerava session in 90+ days as "unverified"

**Effort:** 6-8 hours | **Priority:** P1

### 10.2 Zero Linked Merchants

**Current:** After removing Google Places fallback, `get_merchants_for_intent()` returns 0 merchants because the `charger_merchants` table has no entries. The merchant carousel is empty in production.

**Gap:** The core value proposition (discover merchants while charging) is currently broken in production. Zero merchants are shown.

**Recommendation:**
- **Immediate:** Manually curate merchant links for the top 20 chargers in the user's area (Temple/Round Rock/Austin TX)
- **Short-term:** Build admin tool to link merchants to chargers (drag-and-drop from map)
- **Medium-term:** Use Overpass/OSM API to find restaurants/cafes within 500m of each charger and auto-link
- **Do NOT re-enable Google Places** — per user's explicit instruction

**Effort:** 4-8 hours (manual curation) + 8-12 hours (admin tool) | **Priority:** P0

### 10.3 No Data Contribution from Drivers

**Current:** Drivers consume data but never contribute to it. No mechanism to report corrections, add photos, or update amenity info.
**PlugShare:** Drivers are the primary data source — user-contributed stations, reviews, photos, corrections.

**Gap:** Without driver contributions, data quality degrades over time. With contributions, it improves — network effect.

**Recommendation:**
- Post-session review flow (§5.1) is the primary contribution mechanism
- "Report Issue" on charger detail (§5.3)
- "Suggest Edit" for incorrect charger info (wrong name, wrong location, wrong connector type)
- Photo upload tied to verified sessions

**Effort:** Included in §5.1 and §5.3 estimates | **Priority:** P1

---

## 11. Mobile Platform & Performance Gaps

### 11.1 iOS Safe Area Handling

**Current:** Just fixed — `html, body { background: #ffffff }` and removed `max-w-md mx-auto`. Black bars issue resolved.

**Remaining issues:**
- Bottom sheet may still clip under home indicator on iPhone 15 Pro Max
- Header may not account for dynamic island on iPhone 14 Pro+
- Need to verify `env(safe-area-inset-top)` padding on header

**Effort:** 1-2 hours | **Priority:** P1

### 11.2 No Android Support

**Current:** iOS WKWebView shell only. Web app works in mobile browsers but no native Android shell.
**PlugShare:** Native iOS + Android apps.

**Gap:** ~45% of US smartphone users are on Android. Nerava is invisible to them in app stores.

**Recommendation:**
- Short-term: PWA (Progressive Web App) — already has `manifest.json` and `apple-mobile-web-app-capable`. Add service worker for offline shell.
- Medium-term: Android WebView shell (similar to iOS approach)
- The web app already works in Chrome on Android — just needs store presence

**Effort:** PWA: 4-6 hours, Android shell: 15-20 hours | **Priority:** P2

### 11.3 No Offline Capability

**Current:** Zero offline functionality. App shows blank map without network.
**PlugShare:** Also no offline capability (both have this gap).

**Gap:** Rural charging corridors often have poor cellular coverage. Both apps fail here.

**Recommendation:**
- Service worker cache: cache map tiles for recently viewed areas
- Cache last-known charger data in IndexedDB
- Show stale data with "Last updated X hours ago" badge when offline
- This would be a differentiator over PlugShare

**Effort:** 8-12 hours | **Priority:** P3

### 11.4 No CarPlay / Android Auto

**Current:** None.
**PlugShare:** Apple CarPlay integration (view stations, bookmarks, navigate).

**Gap:** In-car experience is where charger discovery happens most naturally.

**Recommendation:** Future consideration. Requires native iOS CarPlay framework integration in the Xcode project.

**Effort:** 20-30 hours | **Priority:** P3 (future)

---

## 12. PlugShare Feature Parity Matrix

Comprehensive comparison of every PlugShare feature against Nerava's current state:

| # | PlugShare Feature | Nerava Status | Gap Severity | Effort | Priority |
|---|------------------|---------------|--------------|--------|----------|
| 1 | Color-coded charger pins by type | Missing — all pins identical | High | 4-6h | P1 |
| 2 | Charger detail page (specs, amenities, pricing) | Missing — only "merchants at charger" view | Critical | 12-16h | P0 |
| 3 | PlugScore / reliability rating | Missing | High | 6-8h | P1 |
| 4 | User reviews with text + stars + tags | Missing — no reviews table | Critical | 10-14h | P0 |
| 5 | User-uploaded photos | Missing — Google Places photos only | Medium | 8-10h | P2 |
| 6 | Connector type filter | Missing — only amenity filters | High | 4-6h | P1 |
| 7 | Power level filter (kW slider) | Missing — hardcoded 8-stall filter only | High | 3-4h | P1 |
| 8 | Network filter | Missing | Medium | 2-3h | P2 |
| 9 | Real-time availability (network) | Stale `status` field, never updated | High | 15-20h | P2 |
| 10 | Real-time availability (crowd) | Missing | Medium | 3-4h | P1 |
| 11 | Directions with lat/lng | Partial — uses name string, not coords | Medium | 1-2h | P0 |
| 12 | Trip planner with range | Missing | Medium | 25-35h | P3 |
| 13 | Charger bookmarks/favorites | Missing — only merchant favorites | Medium | 4-6h | P1 |
| 14 | Vehicle profile with auto-filter | Partial — VIN stored but not decoded | Medium | 3-4h | P1 |
| 15 | Multiple vehicles per account | Missing — single Tesla only | Low | 4-6h | P3 |
| 16 | Pricing display | Missing | High | 4-6h | P1 |
| 17 | Search by location/address | Missing — name filter only | High | 6-8h | P1 |
| 18 | Map clustering | Missing | Medium | 2-3h | P2 |
| 19 | Satellite/hybrid map tiles | Missing — OSM only | Low | 6-8h | P2 |
| 20 | Station alerts / notifications | Missing | Medium | 6-8h | P2 |
| 21 | Report issue / flag charger | Missing | Medium | 4-6h | P2 |
| 22 | Share charger link | Missing (merchant share exists) | Low | 2-3h | P3 |
| 23 | Driver-to-driver messaging | Missing | Low | 10-15h | P3 |
| 24 | Public driver profiles | Missing — no display name, no stats | Medium | 6-8h | P2 |
| 25 | Check-in status ("Charging Now") | Exists in backend (session_events) but not shown | Medium | 3-4h | P1 |
| 26 | Session receipt / summary email | Missing | Medium | 4-6h | P2 |
| 27 | Onboarding flow | Minimal — location permission only | Medium | 4-6h | P2 |
| 28 | Account identity (email/phone) | Missing — Tesla OAuth only, no contact info | Critical | 8-12h | P0 |
| 29 | Merchant data (linked to chargers) | Broken — 0 merchants after Google Places removal | Critical | 4-8h | P0 |
| 30 | Net cost display (cost minus reward) | Missing — unique Nerava opportunity | High | 3-4h | P1 |

**Summary:** 5 Critical (P0), 14 High (P1), 10 Medium (P2), 6 Low (P3)

---

## 13. What NOT to Build

Per the existing PLUGSHARE_COMPETITIVE_ANALYSIS.md and strategic principles:

| Feature | Why Not |
|---------|---------|
| Manual check-in button | Undermines verified Tesla API story. Nerava's moat is "no self-reporting." |
| "Couldn't Charge" status | Tesla API detects failures automatically via quality_score |
| Home charger sharing | No merchant value. Residential charging doesn't drive the rewards flywheel. |
| Public leaderboards | Incentivizes wasted energy. Reputation tiers are better (private progression). |
| Public activity feed | Privacy-first. Show aggregate "X charging now" not individual driver data. |
| Pay-at-charger (payment network) | Don't become a payment processor. Revenue from campaigns + data, not transaction fees. |
| Banner ads | Stay ad-free. Revenue from sponsor campaigns + merchant subscriptions (Nerava Insights). |
| Full ABRP-style trip planner | Over-engineered. Simple "chargers along route" with merchant highlights is sufficient. |
| Driver-to-driver messaging (now) | Low value, high moderation cost. Build after community has critical mass. |
| Network-level real-time OCPI (now) | High effort, unreliable data. Start with crowd-sourced availability from Nerava sessions. |

---

## 14. Prioritized Roadmap

### Phase 0: Foundation (Week 1) — ~20-30 hours
**Theme:** Fix what's broken, establish identity

| Task | Effort | Impact |
|------|--------|--------|
| Profile completion flow (email, display name, VIN decode) | 8-12h | Unblocks campaigns, payouts, recovery |
| Fix directions to use lat/lng coordinates | 1-2h | Bug fix — wrong navigation destinations |
| Curate merchant links for top 20 chargers (manual) | 4-8h | Restores merchant carousel in production |
| Remove hardcoded 8-stall filter, add user preference | 3-4h | Shows all relevant chargers |

### Phase 1: Charger Discovery (Weeks 2-3) — ~40-55 hours
**Theme:** Make chargers first-class citizens (match PlugShare discovery UX)

| Task | Effort | Impact |
|------|--------|--------|
| Charger detail screen (specs, amenities, merchants, CTA) | 12-16h | Core missing screen |
| Color-coded pins by power level | 4-6h | Visual scanning |
| Connector type + power level filter pills | 6-8h | Essential discovery filter |
| Location/address search (geocoding) | 6-8h | "Show me chargers near Austin Airport" |
| Nerava Score (computed from session data) | 6-8h | Trust signal, PlugShare differentiator |
| Pricing display + net cost after rewards | 4-6h | Unique value proposition display |
| Charger bookmarks/favorites | 4-6h | Quick access to regular chargers |

### Phase 2: Community & Trust (Weeks 4-5) — ~25-35 hours
**Theme:** Build the content flywheel

| Task | Effort | Impact |
|------|--------|--------|
| Post-session review system (stars, tags, comment, photo) | 10-14h | Core PlugShare parity feature |
| "Report Issue" on charger detail | 4-6h | Data quality maintenance |
| "Nerava drivers charging now" on charger detail | 3-4h | Crowd-sourced real-time signal |
| Driver profile enhancement (stats, badges, vehicle) | 6-8h | Account page substance |
| Map clustering at low zoom | 2-3h | Map usability |

### Phase 3: Engagement & Differentiation (Weeks 6-8) — ~30-40 hours
**Theme:** Things PlugShare can't do

| Task | Effort | Impact |
|------|--------|--------|
| Charging statistics dashboard (charts, trends, CO₂) | 8-12h | Unique to Nerava |
| Session receipts (push + email) | 4-6h | Utility + engagement |
| Charger alerts (new campaigns at favorited chargers) | 6-8h | Re-engagement loop |
| Weekly NREL data re-sync | 6-8h | Data freshness |
| Onboarding carousel (3 screens) | 4-6h | First-run experience |
| Network filter + advanced filter panel | 4-6h | Power user feature |

### Phase 4: Moonshots (Weeks 9-12)
**Theme:** Category-defining features

| Task | Effort | Impact |
|------|--------|--------|
| Trip planner MVP (route + chargers + merchants) | 25-35h | Only trip planner with merchant rewards |
| User-uploaded photos (verified from sessions) | 8-10h | Verified photo provenance |
| PWA with offline charger cache | 8-12h | Works where PlugShare doesn't |
| Admin tool for merchant-charger linking | 8-12h | Scalable merchant onboarding |

---

## 15. Appendix: Backend Capability Inventory

### Endpoints Available but Not Used by Frontend

| Endpoint | Purpose | Frontend Status |
|----------|---------|----------------|
| `GET /v1/social/feed` | Community activity feed | Not rendered |
| `GET /v1/social/followers` | Follower list | Not rendered |
| `POST /v1/social/follow` | Follow another user | Not rendered |
| `GET /v1/challenges/active` | Active group challenges | Not rendered |
| `POST /v1/challenges/join` | Join challenge | Not rendered |
| `GET /v1/challenges/leaderboard` | Challenge rankings | Not rendered |
| `GET /v1/analytics/kpis` | KPI dashboard | Admin only |
| `POST /v1/notifications/register` | Push token registration | Implemented in iOS bridge |
| `GET /v1/drivers/profile` | Extended driver profile | Partial use |
| `GET /v1/wallet/timeline` | Activity timeline | Not rendered (only balance shown) |
| `GET /v1/wallet/pass/apple/eligibility` | Apple Wallet pass | Not rendered |
| `POST /v1/arrival/create` | EV arrival flow | Partial (EVArrival screens exist but not wired) |

### Database Tables with No Frontend Exposure

| Table | Purpose | Opportunity |
|-------|---------|-------------|
| `user_preferences` | Food tags, detour prefs, networks | Could power personalized charger ranking |
| `user_consent` | Privacy, marketing consent | Legal compliance |
| `challenges` | Group challenges | Gamification |
| `participations` | Challenge membership | Gamification |
| `follows` | Social graph | Community features |
| `community_periods` | Monthly pool stats | Community pool display |
| `wallet_pass` | Apple/Google Wallet | Physical wallet integration |
| `notification_prefs` | Alert preferences | Notification settings UI |
| `amenity_vote` | Bathroom/wifi ratings | Already in MerchantDetail but could be on charger detail |

### Data Model Gaps (Tables That Don't Exist Yet)

| Missing Table | Purpose | Needed For |
|---------------|---------|------------|
| `charger_reviews` | User reviews of chargers | §5.1 Review system |
| `charger_photos` | User-uploaded charger photos | §4.5 Community photos |
| `charger_reports` | Issue reports (broken, closed, ICE'd) | §5.3 Report mechanism |
| `charger_alerts` | User subscriptions to charger notifications | §8.1 Station alerts |
| `charger_pricing` | Per-kWh and session fee data | §9.1 Pricing display |
| `favorite_chargers` | User charger bookmarks | §6.3 Charger favorites |
| `driver_stats` | Materialized charging statistics | §6.4 Stats dashboard |
| `nerava_scores` | Materialized charger reliability scores | §4.2 Nerava Score |

---

*This report covers 30 identified gaps across 11 categories. The estimated total effort for full remediation is approximately 170-250 hours, spread across 4 phases over 12 weeks. Phase 0 (foundation fixes) and Phase 1 (charger discovery) are critical for achieving basic PlugShare parity and should be prioritized immediately.*
