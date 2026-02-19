# Starting the Driver and Merchant Apps

The landing page CTAs point to the driver app and merchant onboarding portal. These need to be running for the links to work.

## Quick Start

### Option 1: Start Both Apps (Recommended)

Open **3 terminal windows**:

**Terminal 1 - Landing Page:**
```bash
cd apps/landing
npm run dev
# Runs on http://localhost:3000
```

**Terminal 2 - Driver App:**
```bash
cd apps/driver
npm run dev
# Runs on http://localhost:5173
```

**Terminal 3 - Merchant App:**
```bash
cd apps/merchant
npm run dev
# Runs on http://localhost:5174
```

### Option 2: Use Environment Variables

If you want to point to different URLs (e.g., production URLs), create a `.env.local` file in `apps/landing`:

```env
NEXT_PUBLIC_DRIVER_APP_URL=http://localhost:5173
NEXT_PUBLIC_MERCHANT_APP_URL=http://localhost:5174
```

### Option 3: Use Google Forms Fallbacks

If you don't want to run the apps locally, you can temporarily update the CTA links to use Google Forms by modifying `app/components/v2/ctaLinks.ts` to return the form URLs instead.

## Verification

Once all apps are running:
1. Landing page: http://localhost:3000
2. Driver app: http://localhost:5173
3. Merchant app: http://localhost:5174

Click the CTAs on the landing page - they should now work!







