<!-- 560cc729-f276-48ec-b078-0b54e6954874 acb8bf1d-07cd-4d4b-994c-2a68d459d231 -->
# Charger Portal Dashboard Implementation Plan

## Phase 1: Reconnaissance Summary

**Findings from landing-page/ analysis:**

- Next.js 14.2.5 with App Router, TypeScript 5.5.3, Tailwind CSS 3.4.4
- Design tokens: Primary blue (#1e40af) with dark/light/soft variants, secondary gray (#64748b), Inter font
- Button styles: `rounded-lg`, `px-6 py-3`, primary (solid bg-primary), secondary (border-2 border-primary)
- Typography: Headlines `text-3xl`/`text-4xl font-bold`, labels `text-sm`/`text-xs`
- Cards: `rounded-lg shadow-md`, white background
- Spacing: Consistent use of Tailwind spacing scale

## Phase 2: Scaffold charger-portal/ Structure

### 2.1 Base Configuration Files

- Create `charger-portal/` directory at repo root (sibling to `landing-page/`)
- Copy and adapt configuration files:
  - `package.json` - Add Recharts dependency for charts
  - `tsconfig.json` - Same structure as landing-page
  - `tailwind.config.ts` - Copy exact color palette and extend for dashboard needs
  - `postcss.config.mjs` - Same as landing-page
  - `next.config.mjs` - Same as landing-page
  - `.eslintrc.json` - Same as landing-page
  - `.gitignore` - Same as landing-page
  - `next-env.d.ts` - TypeScript definitions

### 2.2 App Structure

```
charger-portal/
├── app/
│   ├── layout.tsx          # Root layout with MainShell
│   ├── page.tsx            # Dashboard Overview (default route)
│   └── globals.css         # Tailwind + Inter font import
├── app/components/
│   ├── layout/
│   │   ├── Sidebar.tsx     # Left navigation sidebar
│   │   ├── TopBar.tsx      # Property selector, date range, user menu
│   │   └── MainShell.tsx   # Wrapper combining Sidebar + TopBar + content
│   ├── ui/
│   │   ├── Button.tsx      # Reuse landing-page button styles
│   │   ├── Card.tsx        # Reusable card component
│   │   ├── Badge.tsx       # Activity type badges
│   │   ├── Tabs.tsx        # Tab component for BuyNovaDialog
│   │   └── Modal.tsx       # Base modal component
│   ├── charts/
│   │   ├── SavingsOverTimeChart.tsx  # Line/area chart using Recharts
│   │   └── OffPeakVsPeakChart.tsx    # Donut/pie chart using Recharts
│   └── dashboard/
│       ├── KpiCards.tsx           # 4 KPI cards row
│       ├── NovaBudgetPanel.tsx    # Budget card with progress bar
│       ├── ActivityFeed.tsx       # Recent activity list
│       ├── SessionsTable.tsx      # Charging sessions table
│       └── BuyNovaDialog.tsx      # Modal with tabs for purchase/auto-topup
├── lib/
│   ├── hooks/
│   │   ├── useSavingsDashboard.ts  # Main dashboard hook
│   │   └── useNovaBudget.ts         # Nova budget operations hook
│   ├── types/
│   │   └── dashboard.ts            # TypeScript interfaces
│   └── mock/
│       └── mockDashboardData.ts    # Realistic mock data for 2-3 properties
└── README.md                       # Setup and API integration notes
```

## Phase 3: Design System Setup

### 3.1 Visual Language Consistency

- Copy `tailwind.config.ts` from landing-page with exact color definitions
- Copy `globals.css` structure, add Inter font import
- Reuse button component styles (PrimaryButton, SecondaryButton, OutlineButton)
- Maintain same border radius (`rounded-lg`), shadows (`shadow-md`), spacing scale

### 3.2 Typography Hierarchy

- Page titles: `text-3xl sm:text-4xl font-bold text-gray-900`
- Section headings: `text-xl font-semibold text-gray-900`
- Labels: `text-sm font-semibold text-gray-700`
- Meta text: `text-xs text-gray-500`

## Phase 4: Core Components Implementation

### 4.1 Layout Components

- **Sidebar.tsx**: Fixed left sidebar with Nerava logo, nav items (Overview, Nova Budgets, Drivers, Reports, Settings), responsive collapse on mobile
- **TopBar.tsx**: Property dropdown selector, date range selector (Last 30 days, This month, etc.), user avatar placeholder
- **MainShell.tsx**: Combines Sidebar + TopBar, handles responsive layout, wraps page content

### 4.2 UI Primitives

- **Button.tsx**: Copy from landing-page, ensure same styles
- **Card.tsx**: Reusable card with `bg-white rounded-lg shadow-md p-6`
- **Badge.tsx**: Activity type badges (SAVINGS, REWARD, TOP-UP) with color coding
- **Tabs.tsx**: Tab component for BuyNovaDialog with active state styling
- **Modal.tsx**: Base modal with overlay, close button, proper ARIA labels

### 4.3 Chart Components

- **SavingsOverTimeChart.tsx**: Recharts LineChart/AreaChart showing daily savings over 30 days, tooltips on hover
- **OffPeakVsPeakChart.tsx**: Recharts PieChart showing session split with legend

## Phase 5: Dashboard Components

### 5.1 KpiCards.tsx

- Grid of 4 cards: Monthly Savings ($1,240), Nova Purchased (12,500 Nova), Rewards Issued ($780), Active EV Drivers (42)
- Each card: value (large, bold), label, subtext
- Responsive: 1 column mobile, 2 columns tablet, 4 columns desktop

### 5.2 NovaBudgetPanel.tsx

- Card showing: Current budget (15,000 Nova / $1,500), Spent (9,200 Nova), Remaining (5,800 Nova), Projected runout date
- Progress bar showing % used
- "Buy Nova" primary button (opens BuyNovaDialog)
- "Manage auto top-up" text link

### 5.3 ActivityFeed.tsx

- List of 6-8 recent events with timestamp, badge (type), description
- Scrollable container
- Events: "Awarded 250 Nova to Alex R. for off-peak charging at 1:00 AM", "Converted 1,000 Nova into Starbucks digital cards", etc.

### 5.4 SessionsTable.tsx

- Table with columns: Driver name, Date & time, Session type (Peak/Off-peak badge), Energy (kWh), Estimated cost, Nova awarded
- Sortable column headers (front-end only)
- 10-15 mock sessions
- Responsive: horizontal scroll on mobile

### 5.5 BuyNovaDialog.tsx

- Modal component with Tabs (One-time purchase, Auto top-up)
- **Tab 1 - One-time purchase**:
  - USD amount input (number)
  - Derived Nova amount (read-only, calculated: 1 USD = 10 Nova)
  - Optional note field
  - "Confirm purchase" button
  - On confirm: simulate delay, update mock state, add activity entry
- **Tab 2 - Auto top-up**:
  - Threshold input (number): "When remaining Nova is below X"
  - Top-up amount (USD or Nova)
  - Frequency dropdown (placeholder)
  - "Save auto top-up settings" button
  - Updates autoTopUpConfig in state

## Phase 6: Data Architecture & Hooks

### 6.1 Type Definitions (lib/types/dashboard.ts)

```typescript
- Property, DateRange, Kpi, DailySavings, SessionSplit, Session, ActivityItem
- NovaBudget, AutoTopUpConfig
- DashboardData (complete dashboard state)
```

### 6.2 Mock Data (lib/mock/mockDashboardData.ts)

- Create 2-3 mock properties with different KPIs:
  - "The Standard at Domain Northside" (high savings, many drivers)
  - "Bridge at the Kenzie" (medium metrics)
  - Optional third property
- Each property has: kpis, dailySavings (30 days), sessionSplit, sessions (15 items), activity (8 items), novaBudget, autoTopUpConfig
- Realistic data patterns (variation in daily savings, mix of peak/off-peak)

### 6.3 Hooks Implementation

- **useSavingsDashboard.ts**:
  - Initializes from mockDashboardData based on selectedProperty
  - Returns: selectedProperty, properties, dateRange, kpis, dailySavings, sessionSplit, sessions, activity, novaBudget, autoTopUpConfig
  - Setters: setSelectedProperty, setDateRange
  - Actions: purchaseNova(amountUsd), updateAutoTopUp(config)
  - Updates mock state in-memory (no API calls)
- **useNovaBudget.ts**:
  - Wraps Nova-specific operations from useSavingsDashboard
  - Exposes: budget, purchaseNova, updateAutoTopUp
  - Conversion rate constant: NOVA_PER_USD = 10

## Phase 7: Main Dashboard Page

### 7.1 app/page.tsx (Overview)

- Uses MainShell layout
- Renders in order:

  1. KpiCards (4 cards row)
  2. Charts row (SavingsOverTimeChart, OffPeakVsPeakChart) - side by side desktop, stacked mobile
  3. Two-column layout: NovaBudgetPanel (left), ActivityFeed (right)
  4. SessionsTable (full width below)

### 7.2 app/layout.tsx

- Root layout with Inter font
- Wraps children in MainShell
- Sets page title: "Nerava Charger Portal - Savings Dashboard"

## Phase 8: Polish & Responsive Design

### 8.1 Responsive Behavior

- Sidebar: Fixed on desktop, collapsible drawer on mobile
- Charts: Stack vertically on mobile (< md breakpoint)
- KPI cards: 1 col mobile, 2 col tablet, 4 col desktop
- Tables: Horizontal scroll on mobile

### 8.2 Loading States

- Skeleton loaders when switching properties/date ranges (simulated delay)
- Loading state in useSavingsDashboard hook

### 8.3 Accessibility

- Semantic HTML (h1, h2, nav, main, etc.)
- ARIA labels on modals, tabs, buttons
- Keyboard navigation support
- Focus management in modals

### 8.4 Transitions

- Hover states on buttons, cards (same as landing-page)
- Smooth transitions for sidebar collapse
- Modal fade-in/out animations

## Phase 9: Documentation

### 9.1 README.md

- Installation: `cd charger-portal && npm install && npm run dev`
- Note: Currently uses mock data only
- API integration points:
  - `useSavingsDashboard` hook - replace mock data initialization with API calls
  - `purchaseNova` function - replace mock update with API POST
  - `updateAutoTopUp` function - replace mock update with API PUT
  - Property/date range changes - add API calls to fetch new data

## Phase 10: Final Quality Checks

### 10.1 Type Safety

- Run `npm run type-check` to verify all TypeScript types are correct
- Ensure all components have proper prop types
- Verify hook return types match expected interfaces

### 10.2 Code Organization

- Verify all imports are clean and use consistent paths
- Ensure no circular dependencies
- Check that mock data is only in `lib/mock/` and hooks

### 10.3 Visual Consistency

- Compare button styles, colors, spacing with landing-page
- Verify charts are readable and match design system
- Check responsive breakpoints match landing-page patterns

## Implementation Order

1. Scaffold base structure (Phase 2)
2. Set up design system (Phase 3)
3. Create UI primitives (Phase 4.2)
4. Build layout components (Phase 4.1)
5. Implement data layer (Phase 6)
6. Build dashboard components (Phase 5)
7. Create charts (Phase 4.3)
8. Assemble main page (Phase 7)
9. Add polish and responsive (Phase 8)
10. Write documentation (Phase 9)
11. Final checks (Phase 10)

### To-dos

- [ ] Create charger-portal/ directory and base Next.js configuration files (package.json, tsconfig.json, tailwind.config.ts, etc.)
- [ ] Copy and adapt design tokens from landing-page (colors, typography, spacing) to charger-portal
- [ ] Create UI component library (Button, Card, Badge, Tabs, Modal) matching landing-page styles
- [ ] Build layout components (Sidebar, TopBar, MainShell) with responsive behavior
- [ ] Define TypeScript types and create realistic mock dashboard data for 2-3 properties
- [ ] Implement useSavingsDashboard and useNovaBudget hooks with mock data integration
- [ ] Build chart components (SavingsOverTimeChart, OffPeakVsPeakChart) using Recharts
- [ ] Create dashboard section components (KpiCards, NovaBudgetPanel, ActivityFeed, SessionsTable)
- [ ] Implement BuyNovaDialog with tabs for one-time purchase and auto top-up configuration
- [ ] Assemble main dashboard page (app/page.tsx) with all components in proper layout
- [ ] Add responsive behavior, loading states, accessibility features, and transitions
- [ ] Create README.md with setup instructions and API integration notes