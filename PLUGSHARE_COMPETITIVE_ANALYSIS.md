# PlugShare Competitive Analysis: Features Nerava Should Adopt

**Prepared for:** James Kirk (Product)
**Date:** February 28, 2026
**Confidential — Internal Use Only**

---

## Executive Summary

PlugShare is the dominant EV charging station discovery app with 2.5M+ users, 350,000+ stations, 5.8M reviews, and 725,000 driver-contributed photos. They have zero vehicle API integration, zero rewards, and zero merchant partnerships — their entire product is built on community-generated data and station discovery UX. Nerava's competitive advantage (verified charging sessions, merchant rewards, campaign engine) is orthogonal to what PlugShare does well. We don't need to become PlugShare — we need to steal the 8-10 features that make their station discovery experience best-in-class and layer them on top of our verified-charging-plus-rewards moat.

This report identifies every adoptable PlugShare feature, maps it against Nerava's current state, assigns priority based on driver value and implementation effort, and explicitly calls out what we should NOT copy.

---

## 1. Map Experience — Charger Info Cards on Tap

### What PlugShare Does

When a user taps a charger pin on the map, a **bottom sheet card** slides up showing:
- Station name
- Distance (miles) and drive time
- PlugScore (1-10 reliability rating)
- Connector type (e.g., "NACS (Tesla)")
- Number of plugs/chargers
- "Directions" button at the bottom
- Map layer toggle (Default / Hybrid / Satellite)
- Dismiss (X) button

The card sits over the map without navigating away. The user can see the charger in geographic context while reading key details. Tapping the card opens the full station detail page.

### What Nerava Has Today

Tapping a charger pin on the Leaflet map shows a **basic popup** with the charger name, network, and campaign reward amount (if applicable). There is no bottom sheet, no distance/drive time, no plug count, no reliability score, no directions button. The popup disappears when tapping elsewhere.

### What We Should Build

**Bottom sheet charger info card** that appears when tapping any charger pin:

| Field | Source | Notes |
|-------|--------|-------|
| Station name | `chargers.name` | Already in DB |
| Distance (mi) | Haversine from device GPS | Already computed for merchants |
| Drive time | Google Distance Matrix or estimate | `distance / 30mph` as fallback |
| Plug types | `chargers.connector_type` | Already in DB |
| Plug count | `chargers.num_chargers` or NREL data | Need to populate |
| Power (kW) | `chargers.power_kw` | Already in DB |
| Nerava Score | Computed from session reviews | New — see Section 4 |
| Network logo | `chargers.charger_network` | Map to icon set |
| "Directions" button | Deep link to Apple Maps / Google Maps | New |
| "View Details" tap target | Navigate to full charger detail | New |
| Nearby Nerava merchants badge | Count of partnered merchants within 500m | Unique to us |

**Nerava twist:** Unlike PlugShare's card, ours should include a **"X merchants nearby"** badge showing how many Nerava-partnered merchants are within walking distance. This reinforces our unique value — PlugShare can tell you where to charge, but only Nerava tells you where to charge AND what to do while you wait.

### Priority: **P0 — Critical**
### Effort: **4-6 hours** (frontend only, data already exists)

---

## 2. Charger Detail View — Rich Station Page

### What PlugShare Does

PlugShare's station detail page is their crown jewel. From the screenshots and research, it includes:

**Header section:**
- Hero photo (community-uploaded, swipeable gallery)
- Bookmark icon overlay on photo
- PlugScore badge + check-in count
- Station name + category (e.g., "Shopping Center")
- Full address with distance and drive time
- "OPEN TO NON-TESLA" accessibility badge (where applicable)

**Action bar:**
- Add Photo
- View Nearby
- Directions
- Report
- Share

**Scrollable detail sections:**
- MY ACTIVITY — Personal check-in history at this station
- DESCRIPTION — Charger count, max power, availability hours, NACS compatibility
- PLUGS — Connector breakdown (type, count, power per type, "View chargers" drill-down)
- COST — Pricing information
- PARKING — Free/paid, type (pull-in, illuminated, covered, garage)
- PARKING DETAILS — Specific access notes
- AMENITIES — Icons for Dining, EV Parking, Restrooms, Shopping
- CHECK-INS — Community reviews with PlugScore explanation, user reviews with vehicle info, helpful votes
- PHOTOS — Community photo gallery with "Add Photo" CTA

### What Nerava Has Today

When a user selects a charger from the home screen, the app shows a **modal with a list of nearby merchants** — and nothing else about the charger itself. No charger photos, no charger specs, no reviews, no amenities, no directions, no pricing. The charger is treated purely as a geographic anchor for merchant discovery.

### What We Should Build

A **dedicated charger detail screen** accessible from the map info card or charger list. Structure:

**1. Hero Section**
- Station photo (from Google Places, NREL, or community uploads — see Section 8)
- Bookmark/favorite icon
- Nerava Score badge (see Section 4)
- Station name, network, address
- Distance + drive time from current location
- "Open to all EVs" / "Tesla only" badge

**2. Quick Actions Bar**
- Directions (deep link to Apple Maps or Google Maps)
- Share (native share sheet)
- Bookmark/Save
- Report issue

**3. Charger Specs Section**
| Field | Source |
|-------|--------|
| Connector types | `chargers.connector_type` |
| Number of plugs | `chargers.num_chargers` or NREL |
| Max power (kW) | `chargers.power_kw` |
| Network | `chargers.charger_network` |
| Pricing | NREL or manual entry |
| Hours | NREL or "24/7" default |
| Access type | Public / Restricted |

**4. Amenities Section**
- Icons for: Restrooms, Food, WiFi, Shopping, Parking type
- Source: NREL station data, Google Places for nearby POIs, or community votes
- Nerava twist: Show **Nerava merchant partners** as highlighted amenities with exclusive deal badges

**5. Nearby Merchants Section (Nerava-unique)**
- Horizontal carousel of partnered merchants within walking distance
- Each card: photo, name, category, walk time, active campaign reward amount
- "View all X merchants" link
- This is what PlugShare CANNOT do — we own the merchant relationship

**6. Session Reviews Section (see Section 5)**
- Community reviews from drivers who charged here via Nerava
- Vehicle type, connector used, session duration, kWh delivered, star rating, comment
- "Was this helpful?" voting

**7. My Activity Section**
- Personal charging history at this station (pulled from `session_events` where `charger_id` matches)
- Last visit date, total sessions, total kWh charged here

### Priority: **P0 — Critical**
### Effort: **8-12 hours** (new screen + backend enrichment endpoint)

---

## 3. Directions Integration — Navigate to Charger

### What PlugShare Does

Every charger has a prominent "Directions" button that deep-links to the user's preferred navigation app (Apple Maps, Google Maps, or Waze). Available from:
- The map info card (bottom sheet)
- The station detail page (action bar)
- The trip planner (per-stop)
- CarPlay

### What Nerava Has Today

The `ChargerCard` component in `PreChargingScreen` has a "Navigate to Charger" button that opens Google Maps. The `MerchantDetailsScreen` has a "Get Directions" button. But the **main map view** has no directions capability — tapping a charger shows a popup with no navigation option. The charger detail modal (which just shows merchants) has no directions button.

### What We Should Build

- **"Directions" button on every charger touchpoint:** map info card, charger detail view, session activity (for past sessions), active session banner
- **Platform-aware deep linking:** iOS → Apple Maps by default (with Google Maps fallback), Android → Google Maps
- **Format:** `maps://` or `comgooglemaps://` scheme with destination lat/lng from `chargers.lat` / `chargers.lng`
- **One-tap:** No intermediate screens. Button press → navigation app opens with route.

### Priority: **P0 — Critical**
### Effort: **2-3 hours** (utility function + button placement across views)

---

## 4. Nerava Score — Our Version of PlugScore

### What PlugShare Does

**PlugScore** is a 1-10 scale reflecting charging station reliability, computed from:
- Positive check-ins (successfully charged) increase score
- Negative check-ins (couldn't charge) decrease score
- Recency-weighted — recent reviews matter more
- Review volume factored in
- Verified accounts weighted higher

It's displayed prominently on every map card, station detail, and search result. It's PlugShare's most recognizable feature and a key driver trust signal.

### What Nerava Has Today

No station reliability score of any kind. The `quality_score` field on `session_events` is an internal anti-fraud metric (0-100), not a user-facing rating. There is no way for drivers to rate a charger or see how reliable it is.

### What We Should Build

**"Nerava Score"** — a charger reliability score with a critical difference from PlugScore: ours is backed by **verified charging data**, not self-reported check-ins.

**Scoring inputs (all from verified sessions):**

| Signal | Weight | Source |
|--------|--------|--------|
| Successful session completion rate | 30% | `session_events` where `ended_reason = 'unplugged'` vs total |
| Average session quality score | 20% | `session_events.quality_score` |
| Average kWh delivered vs expected | 15% | `session_events.kwh_delivered` vs `chargers.power_kw * duration` |
| Community rating (post-session) | 25% | New `charger_reviews` table (see Section 5) |
| Recency decay | 10% | Weight recent sessions more (half-life: 30 days) |

**Display:** 1-10 scale, color-coded badge (green 7+, yellow 4-7, red <4), shown on map info cards and charger detail.

**Nerava advantage over PlugScore:** Our score is computed from API-verified charging sessions, not manual check-ins that anyone can fabricate. When we say a station has a 9.2 Nerava Score, it means 9 out of 10 verified Tesla API sessions completed successfully with expected power delivery. PlugShare can't verify if someone actually charged — they just trust the self-report.

### Priority: **P1 — High**
### Effort: **6-8 hours** (scoring service + DB queries + frontend badge component)

---

## 5. Post-Session Reviews & Comments

### What PlugShare Does

PlugShare's check-in system is their primary community data engine. After manually checking in, users provide:
- Status: Successfully Charged / Couldn't Charge / Charging Now / Waiting
- Vehicle type
- Plug/outlet used
- Duration
- Max power received (kW)
- Free-text comment ("Any tips or suggestions for other drivers?")
- Photo upload (optional)
- "Was this helpful?" voting on other reviews

Reviews are displayed chronologically on the station detail page with the user's name, vehicle, connector, date, and comment text. Other drivers can vote on helpfulness.

### What Nerava Has Today

No post-session review system. Sessions are detected and ended automatically via Tesla API. The session ends, incentives are evaluated, and the driver sees their session card in history — but there's no prompt to leave feedback about the charger experience.

### What We Should Build

**Post-session review prompt** — triggered automatically when a verified session ends (NOT a manual check-in). This is fundamentally better than PlugShare's model because the review is anchored to a real, verified charging event.

**Review flow (appears after session end notification):**

1. **Quick rating:** 1-5 stars (tap, not type)
2. **Quick tags (optional, multi-select):**
   - "Worked perfectly"
   - "Slow charging speed"
   - "Hard to find"
   - "Charger was damaged"
   - "Stall blocked by non-EV"
   - "Good amenities nearby"
   - "Well-lit / safe area"
3. **Comment (optional):** Free-text, 500 char max ("Any tips for other drivers?")
4. **Photo (optional):** Camera or gallery
5. **Submit**

**Key design decisions:**
- Reviews are **opt-in, not required** — prompt appears but can be dismissed
- Reviews are tied to the `session_event_id` for verification
- Only drivers with verified sessions at a charger can review it (prevents fake reviews)
- Display on charger detail page with vehicle type, session duration, kWh, date
- "Was this helpful?" voting (simple up-vote counter)
- Reviews feed into the Nerava Score calculation

**Data model:**
```
charger_reviews:
  id (UUID PK)
  session_event_id (FK → session_events, UNIQUE)
  charger_id (FK → chargers)
  driver_user_id (FK → users)
  rating (1-5)
  tags (JSON array)
  comment (text, nullable)
  photo_url (varchar, nullable)
  helpful_count (int, default 0)
  created_at (timestamp)
```

**What we explicitly do NOT copy from PlugShare:**
- No manual "Check In" button — sessions are always API-detected
- No "Charging Now" / "Waiting to Charge" status — our polling handles this automatically
- No "Couldn't Charge" status as a review type — if you didn't charge, there's no session to review (though we could add a "Report issue" flow independent of sessions)

### Priority: **P0 — Critical** (you specifically called this out)
### Effort: **8-10 hours** (new table, API endpoints, review prompt UI, charger detail integration)

---

## 6. Trip Planner

### What PlugShare Does

PlugShare's Trip Planner lets drivers plan multi-stop road trips with automatic charging stop suggestions:

- Enter origin + destination addresses
- Set vehicle type (auto-pulls range from vehicle garage)
- Set starting battery range
- App calculates route and suggests optimal charging stops
- Map shows route with charger pins along the corridor
- "Show Along Route Only" toggle filters to relevant chargers
- Add/remove/reorder waypoints
- Per-stop details: charger name, distance from route, drive time
- Range radius circle on map (visual range indicator)
- Save trips to account, sync across devices
- Open any stop in preferred navigation app
- 100M+ miles of trips planned on the platform

### What Nerava Has Today

No trip planning feature. No route calculation. No multi-stop journey support. The app is entirely focused on "you're here, what's nearby" — zero support for pre-trip planning.

### What We Should Build

**"Plan a Charge Trip"** — accessible from a new bottom nav tab or the account menu. This is a significant feature build but has huge retention value for road-tripping drivers.

**MVP scope:**

1. **Route input:** Origin + destination (geocoded address input)
2. **Vehicle range:** Pull from Tesla connection (battery capacity, current range) or manual input
3. **Starting charge %:** Manual input or pull from last known Tesla state
4. **Route calculation:** Google Directions API for route polyline
5. **Charger matching:** Query `chargers` table for stations within configurable corridor (e.g., 5mi off-route)
6. **Stop suggestions:** Greedy algorithm — place stops when remaining range drops below 20%, select highest Nerava Score charger within corridor
7. **Results view:**
   - Map with route line + charger stop pins
   - List view: Start → Stop 1 (charger name, distance, estimated arrival) → Stop 2 → Destination
   - Per-stop: tap to see charger detail + nearby Nerava merchants
8. **Save trip:** Store to user account
9. **Navigation:** Per-stop "Directions" deep link

**Nerava twist:** For each suggested charging stop, show **nearby Nerava merchants with active deals**. "Charge at Wolf Ranch Town Center — 3 merchants with exclusive offers." No other trip planner can do this. PlugShare shows chargers along the route; Nerava shows chargers along the route AND tells you where to eat, shop, or work while you charge at each stop.

**V2 enhancements (not MVP):**
- Tesla API integration to pull real-time battery state
- Elevation-aware range estimation
- Weather impact on range
- Save/share trips
- Sync to CarPlay

### Priority: **P2 — Medium** (high value but high effort, not blocking core experience)
### Effort: **20-30 hours** (route API integration, algorithm, new screens, save/sync)

---

## 7. Bookmarks / Saved Chargers

### What PlugShare Does

- Dedicated "Bookmarks" tab in bottom navigation
- Tap bookmark icon on any station photo to save
- Manage saved stations in a list view
- Quick access to station details from bookmarks
- Swipe-to-delete on mobile
- Bookmarks sync across devices and are available in CarPlay

### What Nerava Has Today

- **Merchant favorites** exist (via `FavoritesContext`, persisted to localStorage)
- **No charger favorites/bookmarks** — drivers cannot save frequently-used charging stations
- No dedicated bookmarks tab or screen

### What We Should Build

Extend the existing favorites system to support charger bookmarks:

1. **Bookmark icon on charger touchpoints:** Map info card, charger detail view, session card
2. **Bookmarks section in Account page** with two tabs: "Merchants" (existing) | "Chargers" (new)
3. **Persisted to backend** (not just localStorage) — new `user_bookmarks` table with `type` enum (merchant/charger)
4. **Bookmarked chargers** shown with: name, network, distance, last visit date, Nerava Score

**Nerava twist:** For bookmarked chargers, show a **badge when new merchant deals become available** near that charger. "New offer at your saved charger — Starbucks 15% off while you charge at Market Heights."

### Priority: **P1 — High**
### Effort: **4-6 hours** (extend existing favorites, add charger bookmark type, backend persistence)

---

## 8. Community Photos for Chargers

### What PlugShare Does

- 725,000+ community-uploaded photos
- Users can add photos from the station detail page or during check-in
- Photos show the physical charger, surroundings, parking layout, signage
- Optional captions
- Photo gallery on station detail page
- "Add Photo" icon in action bar

### What Nerava Has Today

No charger photos from community. Station images come from Google Places (for merchants) or NREL data (limited). No way for drivers to upload photos of chargers.

### What We Should Build

**Photo uploads tied to post-session reviews** (Section 5). Rather than a standalone "Add Photo" feature, photos are attached to verified charging sessions. This gives every photo a provenance — we know the driver was actually there.

**Implementation:**
1. Photo capture/select during post-session review flow
2. Upload to S3 (`nerava-charger-photos` bucket)
3. Store URL in `charger_reviews.photo_url`
4. Display in charger detail view photo gallery
5. Show most recent photo as charger hero image (fallback to Google Places / NREL)

**Nerava advantage:** Every photo on Nerava is attached to a verified session. No spam, no fake photos, no photos from people who never charged there. PlugShare has a spam/quality problem because anyone can upload photos without proving they visited.

### Priority: **P2 — Medium**
### Effort: **6-8 hours** (S3 upload, image handling, gallery component)

---

## 9. Advanced Map Filters

### What PlugShare Does

PlugShare has the most comprehensive filter system in the EV charging space:

**Filter categories:**
- Connector type (J1772, CCS, CHAdeMO, Tesla/NACS, Type 2, Wall outlet)
- Charging speed (Level 1, Level 2, DC Fast)
- Minimum power (kW) threshold
- Network (28+ networks: ChargePoint, Tesla, Electrify America, EVgo, etc.)
- Availability (live status where available)
- Access type (public, restricted, residential)
- Cost (free only, pay with PlugShare)
- Parking (accessible, covered, garage, illuminated, pull-through, trailer friendly)
- Amenities (lodging, dining, restrooms, shopping, WiFi, hiking, camping, etc.)
- PlugScore minimum threshold
- Quick filters: "Available", "2+ Stations", "Fast", "Lodging", "Dining", "Free"

Filters persist across sessions and are vehicle-aware (auto-select compatible connectors).

### What Nerava Has Today

The `PrimaryFilters` component shows **merchant amenity filters only**: Bathroom, Food, WiFi, Pets, Music, Patio. These filter merchants, not chargers. There are no charger-specific filters (network, speed, connector type, power level).

### What We Should Build

**Two-tier filter system:**

**Quick filters (horizontal scroll, always visible — like PlugShare's bottom sheet):**
- DC Fast
- Level 2
- Free
- Available Now (if we get live status data)
- Has Merchants (Nerava-unique: only show chargers with nearby partner merchants)
- High Score (Nerava Score 7+)

**Advanced filters (expandable panel):**
- **Network:** Tesla Supercharger, ChargePoint, Electrify America, EVgo, Blink, Other
- **Connector:** NACS/Tesla, CCS, CHAdeMO, J1772
- **Min power:** Slider (25kW → 350kW)
- **Amenities:** Restrooms, Food, WiFi, Shopping
- **Parking:** Free, Covered, Accessible
- **Nerava-exclusive filters:**
  - "Active deals" — chargers with nearby merchants running campaigns
  - "Highest rewards" — sort by max campaign reward amount
  - "Never visited" — chargers you haven't charged at yet

Filters should persist in localStorage and auto-apply on app open.

### Priority: **P1 — High**
### Effort: **6-8 hours** (filter UI + query parameter integration with charger API)

---

## 10. Map Layer Toggle

### What PlugShare Does

Three map layer options accessible from the station detail map view:
- **Default** — standard road map
- **Hybrid** — satellite imagery with road labels overlaid
- **Satellite** — pure satellite/aerial imagery

Toggled via a segmented control at the bottom of the map.

### What Nerava Has Today

Single map layer — OpenStreetMap tiles via Leaflet. No satellite or hybrid view. A layers control icon exists on the map but only toggles marker visibility, not base map tiles.

### What We Should Build

Add tile layer switching to the Leaflet map:
- **Map** (default) — current OpenStreetMap tiles
- **Satellite** — Mapbox satellite or Google satellite tiles
- **Hybrid** — satellite with labels

Toggle via a small button/icon overlay on the map (similar to Google Maps' layers button).

### Priority: **P3 — Low**
### Effort: **1-2 hours** (Leaflet tile layer swap, UI button)

---

## 11. Real-Time Charger Availability

### What PlugShare Does

For networks that share data (Tesla, ChargePoint, EVgo, etc.), PlugShare shows:
- Number of available ports
- Number of in-use ports
- Number of down/broken ports
- "In Use" and "Out of Order" status tags

This data comes from OCPI feeds and direct partnerships with CPOs.

### What Nerava Has Today

The `ChargerCard` component has a `stall_count` display ("X available / Y total") but this appears to be from static NREL data, not real-time status. No live availability tracking.

### What We Should Build

**Phase 1 (leverage existing data):**
- Use our own `session_events` data to show "recently used" status — if a Nerava user is currently charging at a station, show "1 Nerava driver charging here now"
- Aggregate from our own session data: "Last Nerava session: 2 hours ago"

**Phase 2 (external data):**
- Tesla Supercharger availability via Tesla API (we already have OAuth integration)
- OCPI integration for other networks (ChargePoint, EVgo, Electrify America)

**Nerava twist:** Instead of just showing port availability, show **"X drivers earning rewards here right now"** — gamified social proof that makes other drivers want to use Nerava.

### Priority: **P2 — Medium**
### Effort: **Phase 1: 3-4 hours**, Phase 2: 15-20 hours (OCPI integration)

---

## 12. Charger-Level Pricing Display

### What PlugShare Does

Station detail pages show cost information:
- "Payment may be required"
- Specific kWh rates where available
- Parking fee notes
- "Free" badge for no-cost stations
- "Pay with PlugShare" badge for in-app payment support

### What Nerava Has Today

No pricing information displayed for any charger. Drivers have no idea what charging will cost before they arrive.

### What We Should Build

**Pricing section on charger detail view:**
- Pull pricing from NREL AFDC API (many stations include pricing data)
- Display: "~$0.28/kWh" or "Free" or "Pricing varies"
- For Tesla Superchargers: show typical pricing range for the region
- "Pricing may vary by network membership" disclaimer

**Nerava twist:** Show the **net cost after Nerava rewards**: "Charging cost: ~$8.50 | Nerava reward: -$2.00 | **Net cost: ~$6.50**". This makes the value of using Nerava immediately tangible.

### Priority: **P2 — Medium**
### Effort: **4-6 hours** (NREL pricing data, display component, reward offset calculation)

---

## 13. User Profile Enhancements

### What PlugShare Does

The "Me" screen shows:
- Profile photo, name, email
- Vehicle (model, linked to account)
- Stats: Check-ins count, Photos Added count, Locations Added count
- "My Activity" link to personal history
- Charge History
- Messages
- Notifications & Alerts
- Payment Method
- Change Distance Units (miles/km)
- "Subscribe to PlugShare Ad-Free" upsell

### What Nerava Has Today

The Account page shows:
- Name, email, phone (masked)
- Vehicle (Tesla connection status)
- Favorites list
- Share Nerava referral
- Preferences (notifications toggle, distance units)
- Help & Support
- Logout

Missing: personal charging stats on the profile, photo contribution count, community contribution tracking, charge history quick access.

### What We Should Build

Enhance the Account page with a **stats card** at the top:

| Stat | Source |
|------|--------|
| Total sessions | `COUNT(session_events)` for user |
| Total kWh charged | `SUM(session_events.kwh_delivered)` for user |
| Total earned ($) | From wallet ledger |
| Reviews left | `COUNT(charger_reviews)` for user |
| Energy reputation tier + badge | Existing reputation system |
| Member since | `users.created_at` |
| Streak (consecutive days) | Existing streak computation |

This gives drivers a sense of accomplishment and identity within Nerava. PlugShare uses contribution stats to drive community engagement — we should do the same but centered on our rewards system.

### Priority: **P2 — Medium**
### Effort: **3-4 hours** (aggregate queries + profile card UI)

---

## 14. Station Alerts & Notifications

### What PlugShare Does

- Subscribe to individual stations for notifications when:
  - New review/photo posted
  - Station goes offline
  - Station becomes available
- New public station alerts (radius-based)
- Push notifications for all alert types

### What Nerava Has Today

Push notification infrastructure exists (APNs via `NotificationService.swift`, device token registration). Currently used for:
- Incentive earned notifications (post-session)
- Local notifications for session/arrival events

No station-specific alerts or subscription system.

### What We Should Build

**"Notify me" toggle on charger detail view:**
- Alert when a new Nerava merchant deal becomes available near this charger
- Alert when a campaign goes live that rewards charging at this station
- Weekly digest: "Your saved chargers had X sessions this week, Y new reviews"

**Nerava twist:** Alerts are deal-focused, not just status-focused. "New reward at Market Heights: Earn $2.50 per session this week." PlugShare alerts are about charger availability; Nerava alerts are about earning opportunities.

### Priority: **P3 — Low**
### Effort: **6-8 hours** (subscription model, push notification triggers, digest job)

---

## 15. Share Station

### What PlugShare Does

Share button on every station that generates a shareable link. Recipients can view the station on PlugShare's web map without an account.

### What Nerava Has Today

Share functionality exists for merchants (via `MerchantDetailsScreen` — native share sheet or clipboard copy). No share for chargers.

### What We Should Build

- **Share button on charger detail view** — generates a link like `link.nerava.network/charger/{id}`
- Link opens in browser showing charger details + nearby merchants
- UTM tracking for attribution
- Leverage existing `apps/link` redirect infrastructure

### Priority: **P3 — Low**
### Effort: **2-3 hours** (link generation + landing page in `apps/link`)

---

## What We Should NOT Copy from PlugShare

These are deliberate exclusions — features that don't fit Nerava's model or would dilute our product.

### 1. Manual Check-In Button
PlugShare's entire data model depends on users manually tapping "Check In" and self-reporting their charging status. **We should never add this.** Our verified Tesla API detection is categorically better — it's automatic, tamper-proof, and requires zero driver effort. Manual check-in would undermine our data integrity story and the Nerava Score's credibility.

### 2. "Couldn't Charge" Reporting (as a review type)
PlugShare lets users report failed charging attempts as check-ins that negatively impact PlugScore. Since Nerava only creates sessions when the Tesla API confirms active charging, we inherently filter out failed attempts. We should add a separate **"Report an issue"** flow (not tied to a session) for drivers to flag broken chargers, but it should be distinct from the verified review system.

### 3. Home Charger Sharing
PlugShare lets users list private home chargers for community use. This doesn't align with Nerava's merchant-rewards model — there are no merchants near someone's home charger. Skip entirely.

### 4. Leaderboards
PlugShare's "Leaderboards" (visible in their Me tab) gamify check-in volume. For Nerava, leaderboards based on charging volume would incentivize wasted energy and gaming. Our energy reputation tier system (Bronze → Platinum) is a better, more responsible engagement model.

### 5. Activity Feed (public community feed)
PlugShare shows a public activity feed of all nearby check-ins. This has limited value and creates noise. Our session data is private to each driver. We should show "X drivers charging here now" as social proof, not a feed of individual activities.

### 6. Pay with PlugShare
PlugShare's in-app payment (currently EVgo California only) is a charging network play. Nerava is a rewards layer, not a payment network. We should integrate with existing payment systems (Tesla in-car, ChargePoint app, etc.) rather than trying to become a payment intermediary.

### 7. Ad-Supported Model / Banner Ads
PlugShare shows banner ads throughout the app (visible in multiple screenshots — Shell Recharge ads). Nerava should remain ad-free. Our revenue comes from merchant campaigns and data subscriptions, not display advertising. Ads would cheapen the premium feel of a rewards app.

### 8. Distance Unit Toggle (Already Have)
Already implemented in Account preferences. No action needed.

---

## Implementation Roadmap

### Phase 1: Foundation (Weeks 1-2) — Make Chargers First-Class Citizens

| Feature | Section | Effort | Impact |
|---------|---------|--------|--------|
| Map info card (bottom sheet on tap) | 1 | 4-6h | Transforms map from merchant-only to charger+merchant |
| Charger detail view | 2 | 8-12h | Gives chargers a real identity in the app |
| Directions integration | 3 | 2-3h | Most requested basic utility feature |
| Post-session review prompt | 5 | 8-10h | Seeds community content, enables Nerava Score |

**Phase 1 total: ~22-31 hours**

### Phase 2: Intelligence Layer (Weeks 3-4) — Make Data Actionable

| Feature | Section | Effort | Impact |
|---------|---------|--------|--------|
| Nerava Score | 4 | 6-8h | Trust signal on every charger, unique differentiator |
| Charger bookmarks | 7 | 4-6h | Retention through saved locations |
| Advanced map filters | 9 | 6-8h | Power user discovery, reduces friction |
| Profile stats card | 13 | 3-4h | Engagement through achievement visibility |

**Phase 2 total: ~19-26 hours**

### Phase 3: Depth (Weeks 5-8) — Build the Moat

| Feature | Section | Effort | Impact |
|---------|---------|--------|--------|
| Community photos | 8 | 6-8h | Visual trust, content flywheel |
| Real-time availability (Phase 1) | 11 | 3-4h | Utility from our own session data |
| Charger pricing display | 12 | 4-6h | Pre-arrival decision support |
| Station alerts | 14 | 6-8h | Re-engagement through deal notifications |
| Share charger | 15 | 2-3h | Organic growth |
| Map layer toggle | 10 | 1-2h | Polish |

**Phase 3 total: ~22-31 hours**

### Phase 4: Moonshot (Weeks 9-12) — Trip Planner

| Feature | Section | Effort | Impact |
|---------|---------|--------|--------|
| Trip planner MVP | 6 | 20-30h | Road trip use case, massive retention driver |
| Real-time availability (Phase 2 — OCPI) | 11 | 15-20h | Network-level live data |

**Phase 4 total: ~35-50 hours**

---

## Strategic Summary

PlugShare built a $25M business (EVgo acquisition price) on community-generated station data and a great map UX. They have zero verified charging data, zero merchant partnerships, and zero driver rewards. Nerava has all three but lacks PlugShare's station discovery depth.

The play is surgical: steal PlugShare's charger detail richness, their review system concept (but make it verified-only), their trip planner utility, and their filtering power. Layer all of it on top of our verified-session and merchant-rewards moat. The result is an app where drivers come for the charger discovery (table stakes), stay for the rewards (differentiation), and generate verified behavioral data (the real business).

Every feature we adopt from PlugShare should be twisted to highlight what makes Nerava unique:
- Their map card shows distance → ours shows distance + "3 merchants with deals"
- Their PlugScore is self-reported → our Nerava Score is API-verified
- Their check-in is manual → our review is triggered by a real session
- Their trip planner shows chargers → ours shows chargers + merchant deals at each stop
- Their photos are from anyone → our photos are from verified chargers

We don't need to out-PlugShare PlugShare. We need to match their station discovery UX and then beat them on everything that happens after the driver plugs in.

---

*This document is a competitive feature analysis for internal planning. PlugShare is a trademark of Recargo, Inc. (EVgo). All feature descriptions are based on public app screenshots, help center documentation, and published materials.*
