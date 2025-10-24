# Nerava Mobile UI

A modern, mobile-first web application for EV charging rewards and social features.

## Development Setup

### Backend
1. Start the FastAPI backend:
   ```bash
   cd ../nerava-backend-v9
   uvicorn app.main_simple:app --reload --port 8001
   ```

2. Verify backend is running:
   ```bash
   curl http://127.0.0.1:8001/health
   ```

### Frontend
1. Open the app in your browser:
   ```
   http://127.0.0.1:8001/app/
   ```

## Testing with Playwright

### Setup
```bash
npm install
npx playwright install
```

### Run Tests
```bash
# Run tests in headless mode
npm run test:ui

# Run tests with visible browser (watch the UI)
npm run test:ui:headed

# Debug mode (step through tests)
npm run test:ui:debug

# View test report
npm run test:ui:report
```

### Test Features
- **Explore Page**: Map loading, perk card display, navigation to Claim
- **Tab Navigation**: Explore → Charge → Wallet → Me → Explore
- **Social Flow**: Follow/unfollow, reward events, community feed
- **Backend Integration**: API calls for social features

### Test Outputs
- **Videos**: `videos/` - Recorded test sessions
- **Traces**: `traces/` - Detailed execution traces
- **Screenshots**: `test-results/` - Failure screenshots
- **Report**: `playwright-report/` - HTML test report

## Features

### 5-Tab Navigation
- **Explore**: Minimal route + single perk card
- **Charge**: Community activity feed + follow/unfollow
- **Claim**: Map with geofence claim areas
- **Wallet**: Balance, rewards, community pool
- **Me**: Profile and preferences

### Social Features
- Follow/unfollow other users
- Community pool (10% of rewards shared)
- Activity feed with real-time updates
- Leaderboard and social proof

### Technical Stack
- **Frontend**: Vanilla JS with modular architecture
- **Backend**: FastAPI with SQLAlchemy
- **Maps**: Leaflet with routing
- **Testing**: Playwright with video/trace recording