# Nerava UI

New frontend app built with React + TypeScript + Vite + Tailwind CSS, matching latest Figma designs.

## Tech Stack

- **React 19** with TypeScript
- **Vite** for build tooling
- **Tailwind CSS** for styling
- **React Router** for routing
- **TanStack Query** for data fetching and caching
- **Vitest** + **React Testing Library** for testing

## Project Structure

```
nerava-ui/
├── src/
│   ├── components/        # React components
│   │   ├── WhileYouCharge/
│   │   ├── MerchantDetails/
│   │   ├── WalletSuccess/
│   │   └── shared/
│   ├── hooks/            # Custom React hooks
│   ├── services/         # API client (TanStack Query)
│   ├── types/            # TypeScript types
│   ├── App.tsx           # Main app with routing
│   └── main.tsx          # Entry point
├── tests/                # Unit tests (Vitest)
└── e2e/                  # E2E tests (Playwright)
```

## Routes

- `/wyc` - While You Charge screen (default)
- `/m/:merchantId` - Merchant Details screen

## Development

### Prerequisites

- Node.js 18+
- Backend running on `http://localhost:8001`

### Start Development Server

```bash
npm install
npm run dev
```

App will be available at `http://localhost:5173`

### Run Tests

```bash
# Unit tests
npm test

# Tests with UI
npm run test:ui
```

### Build for Production

```bash
npm run build
```

Output will be in `dist/` directory.

## Environment Variables

Create a `.env` file (optional):

```env
VITE_API_BASE_URL=http://localhost:8001
```

## API Integration

The app calls these backend endpoints:

- `POST /v1/intent/capture` - Capture charging intent with geolocation
- `GET /v1/merchants/{merchant_id}` - Get merchant details
- `POST /v1/wallet/pass/activate` - Activate wallet pass

## Testing

### Unit Tests

Tests are written with Vitest + React Testing Library:

- `tests/components/WhileYouChargeScreen.test.tsx` - Tests WYC screen rendering
- `tests/components/MerchantDetailsScreen.test.tsx` - Tests merchant details and wallet activation
- `tests/components/WalletSuccessModal.test.tsx` - Tests success modal
- `tests/hooks/useGeolocation.test.ts` - Tests geolocation hook

### E2E Tests

E2E tests are in `/e2e/tests/` and use Playwright. See `/e2e/README.md` for details.

## Design Notes

- **No maps** - Map dependencies removed
- **No infinite scroll** - While You Charge screen fits in viewport
- **Moment of charge** - UI focuses on the charging moment, not browsing
