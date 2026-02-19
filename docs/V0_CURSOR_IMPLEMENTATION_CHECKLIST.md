# V0 Web-First EV Arrival — Cursor Implementation Checklist

Each item is a self-contained Cursor prompt. Execute in order. Copy the prompt block into Cursor.

---

## Task 1: Session Expiry Background Task

```
You are Cursor. Add a background task that expires stale arrival sessions.

File to modify: backend/app/lifespan.py (or backend/app/main.py if lifespan.py doesn't have an appropriate hook)

Pattern to follow: Look at how the existing lifespan context manager works in lifespan.py.

Requirements:
1. Create an async background task that runs every 60 seconds
2. Query arrival_sessions where status IN ('pending_order', 'awaiting_arrival', 'arrived', 'merchant_notified') AND expires_at < now()
3. Update those rows to status = 'expired', set completed_at = now()
4. Log the count of expired sessions
5. Start this task during app lifespan startup, cancel on shutdown
6. Use the existing get_db() or async session pattern from backend/app/db.py

Import the ArrivalSession model from backend/app/models/arrival_session.py.
Use sqlalchemy update() with a WHERE clause — do NOT load rows into Python.

Add a PostHog event capture for each expired session: event name "ev_arrival.expired", properties: { session_id, merchant_id, created_at, expires_at }.
Use the analytics pattern from backend/app/services/analytics.py.
```

---

## Task 2: Web Confirm Support in Arrival Router

```
You are Cursor. Modify the confirm-arrival endpoint to support web-only confirmations.

File: backend/app/routers/arrival.py

Find the POST /v1/arrival/{session_id}/confirm-arrival endpoint.

Changes:
1. Add an optional field to the request schema: web_confirm: bool = False
2. When web_confirm=True:
   - charger_id is no longer required (make it Optional)
   - If charger_id is missing, find the nearest charger to the given lat/lng from the chargers table (within 500m)
   - If a nearby charger is found, use it for the distance check
   - If no charger is nearby AND no lat/lng provided, allow confirmation but set arrival_accuracy_m = None
   - Add a PostHog property: confirmation_method = "web_manual" (vs "native_geofence" for the existing path)
3. When web_confirm=False (default): behavior unchanged — charger_id is required

Look at the existing charger lookup pattern in backend/app/routers/charge_context.py for how to query chargers by location.

Do NOT change the existing native geofence path behavior. Only add the web_confirm=True branch.
```

---

## Task 3: Billing CSV Export Endpoint

```
You are Cursor. Add a billing CSV export endpoint for admins.

File: backend/app/routers/admin_domain.py

Add this endpoint:
GET /v1/admin/billing-export?month=YYYY-MM

Requirements:
1. Auth: require admin user (use the existing admin auth dependency from this file)
2. Query billing_events joined with arrival_sessions and merchants for the given month
3. Return CSV with headers: session_id, merchant_id, merchant_name, driver_id, order_number, order_total_cents, fee_bps, billable_cents, total_source, completed_at
4. Use StreamingResponse with media_type="text/csv"
5. Set Content-Disposition header: attachment; filename="nerava-billing-{month}.csv"
6. If month param is missing or invalid, return 400
7. Add PostHog event: ev_arrival.billing_export with properties: { month, row_count, total_billable_cents }

Import BillingEvent from backend/app/models/billing_event.py
Import ArrivalSession from backend/app/models/arrival_session.py
Import Merchant from backend/app/models/while_you_charge.py (the merchants table model)

Use the csv module from Python stdlib. Write to io.StringIO, then return as StreamingResponse.
```

---

## Task 4: Daily Session Rate Limit

```
You are Cursor. Add a daily rate limit to the arrival create endpoint.

File: backend/app/routers/arrival.py

Find the POST /v1/arrival/create endpoint.

Add at the top of the handler (after auth, before creating the session):
1. Count completed arrival sessions for this driver_id today (WHERE created_at >= start_of_today AND status IN ('completed', 'completed_unbillable'))
2. If count >= 3, return 429 with detail: "Maximum 3 EV Arrivals per day. Try again tomorrow."
3. Use the driver's timezone or UTC for "today" calculation

This prevents session farming. Keep it simple — a SQL count query is fine.
```

---

## Task 5: Wire EVArrival into DriverHome

```
You are Cursor. Wire the EVArrival components into the driver app.

File: apps/driver/src/components/DriverHome/DriverHome.tsx

Context: 5 EVArrival components exist at apps/driver/src/components/EVArrival/:
- ModeSelector.tsx
- VehicleSetup.tsx
- ConfirmationSheet.tsx
- ActiveSession.tsx
- CompletionScreen.tsx

These components are ALREADY BUILT but not imported or rendered anywhere.

Changes:
1. Import ModeSelector from '../EVArrival/ModeSelector'
2. Add state: const [showEVArrival, setShowEVArrival] = useState(false)
3. Add state: const [selectedMerchantForArrival, setSelectedMerchantForArrival] = useState<string | null>(null)
4. On each merchant card, add a button "Add EV Arrival" that sets showEVArrival=true and selectedMerchantForArrival=merchant.id
5. When showEVArrival is true, render <ModeSelector merchantId={selectedMerchantForArrival} onClose={() => setShowEVArrival(false)} />
6. Check if there's an active arrival session (call GET /v1/arrival/active on mount). If active, show ActiveSession component instead of the merchant list.

Look at the existing merchant card rendering in DriverHome to understand the card layout. Add the "Add EV Arrival" button as a primary CTA below the existing card content.

Use the fetchAPI function from apps/driver/src/services/api.ts for API calls.
Follow the existing Tailwind styling patterns in the file.
```

---

## Task 6: Add /arrival Route

```
You are Cursor. Add an /arrival route to the driver app.

File: apps/driver/src/App.tsx

Changes:
1. Import ActiveSession from './components/EVArrival/ActiveSession'
2. Add a new Route: <Route path="/arrival" element={<ActiveSession />} />
3. Place it alongside the existing routes (before the catch-all if one exists)

This route is used when a driver returns to the app after placing an order externally.
The ActiveSession component should handle the case where no active session exists (redirect to / or show empty state).
```

---

## Task 7: Add "Add EV Arrival" to Merchant Detail

```
You are Cursor. Add an "Add EV Arrival" CTA to the merchant detail screen.

File: apps/driver/src/components/MerchantDetails/MerchantDetailsScreen.tsx
(or MerchantDetailModal.tsx — check which one renders the merchant detail view)

Changes:
1. Add a primary button "Add EV Arrival" below the merchant info
2. Style it as the primary CTA: bg-blue-600 text-white rounded-xl py-3 px-6 w-full font-semibold
3. On tap, navigate to the EVArrival flow or trigger a callback to DriverHome
4. If the merchant has an ordering_url, also show a secondary button "View Menu" that opens the URL in a new tab
5. If there's already an active session for this merchant, show "View Active Arrival" instead

Use the existing button patterns from apps/driver/src/components/shared/Button.tsx.
Check the merchant data shape from the API response to find ordering_url.
```

---

## Task 8: Web Geolocation + Polling in ActiveSession

```
You are Cursor. Add web geolocation confirmation and polling to ActiveSession.

File: apps/driver/src/components/EVArrival/ActiveSession.tsx

Changes:

1. POLLING: Add useEffect that polls GET /v1/arrival/active every 5 seconds.
   - Use setInterval with cleanup in the return function
   - When the session status changes to 'completed' or 'completed_unbillable', stop polling and show CompletionScreen
   - When status is 'expired' or 'canceled', stop polling and redirect to home

2. WEB GEOLOCATION CONFIRM: Check if running in native mode using the useNativeBridge hook.
   When NOT native (isNative === false from apps/driver/src/hooks/useNativeBridge.ts):
   - Show an "I'm at the charger" button when status is 'awaiting_arrival'
   - On tap, call navigator.geolocation.getCurrentPosition()
   - On success: POST /v1/arrival/{id}/confirm-arrival with { lat, lng, accuracy_m: coords.accuracy, web_confirm: true }
   - On geolocation denied: Show "I'm at the charger anyway" fallback button that calls confirm-arrival with { web_confirm: true } (no lat/lng)
   - Show loading spinner while geolocation is resolving

3. ORDERING LINK: If the session response includes ordering_url, show "Order from {merchant_name}" button that opens the URL in a new tab (window.open(url, '_blank'))

Use fetchAPI from apps/driver/src/services/api.ts for all API calls.
Import useNativeBridge from apps/driver/src/hooks/useNativeBridge.ts.
Follow existing Tailwind patterns in the file.
```

---

## Task 9: Merchant Portal — Hide Email Toggle + Add Export

```
You are Cursor. Update the merchant portal EVArrivals tab.

File: apps/merchant/app/components/EVArrivals.tsx

Changes:
1. Find the email notification toggle/checkbox. Replace it with static text: "Email notifications — Coming soon"
2. Add a "Download Billing CSV" button at the top of the arrivals list (only visible if the user has admin role or if there are billing events)
3. The download button should call GET /v1/admin/billing-export?month={current_month} and trigger a file download
4. Use the existing fetchAPI pattern from apps/merchant/app/services/api.ts

For the CSV download:
```typescript
const downloadCSV = async () => {
  const month = new Date().toISOString().slice(0, 7); // YYYY-MM
  const response = await fetch(`${API_BASE}/v1/admin/billing-export?month=${month}`, {
    headers: { Authorization: `Bearer ${token}` }
  });
  const blob = await response.blob();
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `nerava-billing-${month}.csv`;
  a.click();
  URL.revokeObjectURL(url);
};
```

Follow existing styling patterns in the file.
```

---

## Task 10: Notification Service Email Warning

```
You are Cursor. Update the notification service to log a clear warning when email is attempted.

File: backend/app/services/notification_service.py

Find the send_email_notification function (or email-related code path).
Change it to:
1. Log a WARNING: "Email notifications not implemented in V0. Merchant {merchant_id} has notify_email=True but no email will be sent."
2. Return False (already does this)
3. Add a PostHog event: "merchant.email_notification_skipped" with { merchant_id }

This makes it visible in logs and analytics when merchants have email enabled but aren't receiving anything.
```

---

## Task 11: Post-Claim Google Maps Instructions

```
You are Cursor. Add Google Maps Business Profile instructions after successful claim.

File: apps/merchant/app/components/ClaimBusiness.tsx

Find the success state after claim verification completes.

Add a new section after the success message:

```tsx
<div className="mt-6 p-4 bg-blue-50 rounded-xl">
  <h3 className="font-semibold text-blue-900 mb-2">Boost your visibility</h3>
  <p className="text-sm text-blue-800 mb-3">
    Add a link to your Google Business Profile so EV drivers can find you:
  </p>
  <div className="bg-white rounded-lg p-3 border border-blue-200">
    <code className="text-xs text-gray-700 break-all select-all">
      https://app.nerava.network/m/{merchantSlug}
    </code>
  </div>
  <ol className="mt-3 text-sm text-blue-800 space-y-1 list-decimal list-inside">
    <li>Open Google Business Profile Manager</li>
    <li>Go to "Edit profile" → "Contact"</li>
    <li>Add website link with label "Order ahead for EV drivers"</li>
    <li>Save</li>
  </ol>
</div>
```

Get the merchantSlug from the claim flow state or localStorage('merchant_id').
This is informational only — no API call needed.
```

---

## Execution Order

Run tasks 1-4 (backend) first, then 5-8 (driver frontend), then 9-11 (merchant portal + polish). Each task is independent within its group and can be run in parallel if desired.

**Verification after each task:**
- Task 1: Check server logs for "Expired N sessions" messages
- Task 2: `curl -X POST /v1/arrival/{id}/confirm-arrival -d '{"web_confirm": true, "lat": 30.26, "lng": -97.74}'`
- Task 3: `curl /v1/admin/billing-export?month=2026-02 -H "Authorization: Bearer {token}"`
- Task 4: Create 4 sessions → 4th returns 429
- Task 5: Open driver app → merchant cards show "Add EV Arrival"
- Task 6: Navigate to /arrival → ActiveSession renders
- Task 7: Open merchant detail → "Add EV Arrival" button visible
- Task 8: ActiveSession polls, "I'm here" button works
- Task 9: EVArrivals tab → email says "Coming soon", download button works
- Task 10: Check logs for email warning
- Task 11: Complete claim → Google Maps instructions visible
