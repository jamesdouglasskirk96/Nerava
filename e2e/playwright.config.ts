import { defineConfig, devices } from '@playwright/test'

export default defineConfig({
  testDir: './tests',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: process.env.CI ? 'github' : 'html',
  use: {
    // Use Docker Compose routes when DOCKER_COMPOSE env var is set
    baseURL: process.env.DOCKER_COMPOSE ? 'http://localhost/app' : 'http://localhost:5173',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
  ],
  webServer: [
    {
      command: 'cd ../backend && python -m uvicorn app.main_simple:app --port 8001',
      url: 'http://localhost:8001/healthz',
      reuseExistingServer: !process.env.CI,
      env: {
        ENV: 'test',
        OTP_PROVIDER: 'stub',
        MOCK_PLACES: 'true',
        DEMO_STATIC_DRIVER_ENABLED: 'true',
      },
    },
    {
      command: 'cd ../apps/landing && npm run dev',
      url: 'http://localhost:3000',
      reuseExistingServer: !process.env.CI,
    },
    {
      command: 'cd ../apps/driver && npm run dev',
      url: 'http://localhost:5173',
      reuseExistingServer: !process.env.CI,
      env: {
        VITE_API_BASE_URL: 'http://localhost:8001',
        VITE_MOCK_MODE: 'false',
        VITE_ENV: 'test',
      },
    },
    {
      command: 'cd ../apps/merchant && npm run dev',
      url: 'http://localhost:5174',
      reuseExistingServer: !process.env.CI,
      env: {
        VITE_API_BASE_URL: 'http://localhost:8001',
        VITE_MOCK_MODE: 'false',
        VITE_ENV: 'test',
      },
    },
    {
      command: 'cd ../apps/admin && npm run dev',
      url: 'http://localhost:5175',
      reuseExistingServer: !process.env.CI,
      env: {
        VITE_API_BASE_URL: 'http://localhost:8001',
        VITE_MOCK_MODE: 'false',
        VITE_ENV: 'test',
      },
    },
  ],
})

