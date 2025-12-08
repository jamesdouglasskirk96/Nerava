# Nerava Charger Portal

Charger Owner Portal - Savings Dashboard for managing EV charging costs and driver rewards.

## Overview

This is a standalone Next.js application that provides charger owners with a comprehensive dashboard to:
- View savings from off-peak charging incentives
- Manage Nova budgets and purchases
- Monitor driver activity and rewards
- Track charging sessions and energy usage

## Technology Stack

- **Next.js 14+** with App Router
- **TypeScript** for type safety
- **Tailwind CSS** for styling (matching landing-page design system)
- **Recharts** for data visualization

## Getting Started

### Prerequisites

- Node.js 18+ and npm

### Installation

```bash
cd charger-portal
npm install
```

### Development

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) in your browser.

### Build for Production

```bash
npm run build
npm start
```

### Type Checking

```bash
npm run type-check
```

### Linting

```bash
npm run lint
```

## Project Structure

```
charger-portal/
├── app/
│   ├── components/
│   │   ├── layout/          # Sidebar, TopBar, MainShell, DashboardLayout
│   │   ├── ui/              # Button, Card, Badge, Tabs, Modal
│   │   ├── charts/          # SavingsOverTimeChart, OffPeakVsPeakChart
│   │   └── dashboard/        # KpiCards, NovaBudgetPanel, ActivityFeed, SessionsTable, BuyNovaDialog
│   ├── layout.tsx            # Root layout
│   ├── page.tsx              # Dashboard Overview page
│   └── globals.css           # Tailwind styles
├── lib/
│   ├── hooks/
│   │   ├── useSavingsDashboard.ts  # Main dashboard data hook
│   │   └── useNovaBudget.ts         # Nova budget operations hook
│   ├── types/
│   │   └── dashboard.ts             # TypeScript interfaces
│   └── mock/
│       └── mockDashboardData.ts     # Mock data for 2-3 properties
└── README.md
```

## Current Status

**All data is currently mocked.** The application uses realistic mock data stored in `lib/mock/mockDashboardData.ts` and managed through React hooks. No real API calls are made.

## API Integration Points

To connect to real backend APIs, update the following:

### 1. Data Fetching (`lib/hooks/useSavingsDashboard.ts`)

**Current:** Initializes from `mockDashboardData.ts`

**To integrate:**
- Replace mock data initialization with API calls:
  ```typescript
  // Replace this:
  const baseData = mockDashboardData[selectedPropertyId]
  
  // With API call:
  const { data: baseData } = await fetch(`/api/v1/dashboard/${selectedPropertyId}?dateRange=${dateRange}`)
  ```

**Key functions to update:**
- `setSelectedProperty()` - Add API call to fetch property data
- `setDateRange()` - Add API call to filter data by date range
- Initial data load - Replace `mockDashboardData` with API fetch

### 2. Nova Purchase (`lib/hooks/useSavingsDashboard.ts`)

**Current:** Updates in-memory state

**To integrate:**
```typescript
// In purchaseNova function, replace mock update with:
const response = await fetch('/api/v1/nova/purchase', {
  method: 'POST',
  body: JSON.stringify({ amountUsd, note }),
})
const result = await response.json()
// Update state from API response
```

### 3. Auto Top-up Configuration (`lib/hooks/useSavingsDashboard.ts`)

**Current:** Updates in-memory state

**To integrate:**
```typescript
// In updateAutoTopUp function, replace mock update with:
const response = await fetch('/api/v1/nova/auto-topup', {
  method: 'PUT',
  body: JSON.stringify(config),
})
const result = await response.json()
// Update state from API response
```

### 4. Real-time Updates

Consider adding:
- WebSocket connection for live activity feed updates
- Polling for dashboard data refresh
- Server-sent events for real-time notifications

## Mock Data Structure

The mock data includes:
- **2 properties** with different performance metrics
- **30 days** of daily savings data
- **15 charging sessions** per property
- **8 activity items** per property
- **Nova budget** with spent/remaining calculations
- **Auto top-up configuration**

All data is structured to match the TypeScript interfaces in `lib/types/dashboard.ts`.

## Design System

The portal uses the same visual language as `landing-page/`:
- **Primary color:** `#1e40af` (EV blue)
- **Typography:** Inter font, consistent heading hierarchy
- **Components:** Matching button styles, card shadows, spacing
- **Responsive:** Mobile-first design with breakpoints

## Features

- ✅ Fully responsive dashboard (mobile, tablet, desktop)
- ✅ Interactive charts (Savings Over Time, Session Distribution)
- ✅ Real-time KPI cards
- ✅ Nova budget management with purchase dialog
- ✅ Auto top-up configuration
- ✅ Activity feed with timestamps
- ✅ Sortable sessions table
- ✅ Loading states and skeletons
- ✅ Accessible UI (ARIA labels, keyboard navigation)

## Future Enhancements

- [ ] Connect to real backend APIs
- [ ] Add authentication/authorization
- [ ] Real-time data updates
- [ ] Export reports functionality
- [ ] Advanced filtering and date range selection
- [ ] Driver management interface
- [ ] Settings page implementation

## Notes

- The conversion rate is currently hardcoded: `1 USD = 10 Nova` (defined in `lib/types/dashboard.ts`)
- All calculations (projected runout dates, percentages) are client-side only
- Property switching and date range changes simulate loading delays for better UX
- The sidebar navigation items are visual only (no routing implemented yet)

## License

Part of the Nerava monorepo. All rights reserved.

