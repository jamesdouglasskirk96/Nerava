import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { MemoryRouter, Routes, Route } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MerchantDetailsScreen } from '../../src/components/MerchantDetails/MerchantDetailsScreen'

// Mock fetch
global.fetch = vi.fn()

// Mock geolocation — the component uses getCurrentPosition in activation flows
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
  watchPosition: vi.fn().mockReturnValue(1),
  clearWatch: vi.fn(),
}

describe('MerchantDetailsScreen', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
        mutations: { retry: false },
      },
    })
    vi.clearAllMocks()

    // Simulate authenticated user
    localStorage.setItem('access_token', 'test-token')

    // Mock geolocation — resolve immediately with test coordinates
    // @ts-ignore
    global.navigator.geolocation = mockGeolocation
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 30.2672,
          longitude: -97.7431,
          accuracy: 50,
        },
      })
    })
  })

  afterEach(() => {
    localStorage.clear()
  })

  it('renders merchant details and Activate Exclusive triggers modal on success', async () => {
    const user = userEvent.setup()

    // Mock merchant details response (matches MerchantDetailsResponseSchema)
    const mockMerchantDetails = {
      merchant: {
        id: 'mock_asadas_grill',
        name: 'Asadas Grill',
        category: 'Restaurant • Food',
        photo_url: 'https://example.com/photo.jpg',
        address: '123 Main St, Austin, TX',
        rating: 4.5,
        price_level: 2,
      },
      moment: {
        label: '3 min walk',
        distance_miles: 0.2,
        moment_copy: 'Fits your charge window',
      },
      perk: {
        title: 'Happy Hour',
        badge: 'Happy Hour',
        description: 'Show your pass to access Happy Hour.',
      },
      wallet: {
        can_add: true,
        state: 'INACTIVE',
      },
      actions: {
        add_to_wallet: true,
        get_directions_url: 'https://maps.google.com/?q=30.2680,-97.7435',
      },
    }

    // Mock exclusive activation response
    const mockActivateResponse = {
      status: 'ok',
      exclusive_session: {
        id: 'exc-123',
        merchant_id: 'mock_asadas_grill',
        charger_id: 'canyon_ridge_tesla',
        expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
        activated_at: new Date().toISOString(),
        remaining_seconds: 3600,
      },
    }

    // @ts-ignore — first call returns merchant details, second returns activation
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockMerchantDetails,
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockActivateResponse,
      })

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/m/mock_asadas_grill?session_id=test-session']}>
          <Routes>
            <Route path="/m/:merchantId" element={<MerchantDetailsScreen />} />
          </Routes>
        </MemoryRouter>
      </QueryClientProvider>
    )

    // Wait for merchant details to load
    await waitFor(
      () => {
        expect(screen.getByText('Asadas Grill')).toBeInTheDocument()
      },
      { timeout: 3000 },
    )

    expect(screen.getByText('Restaurant • Food')).toBeInTheDocument()

    // Click Activate Exclusive button
    const activateButton = screen.getByRole('button', { name: /Activate Exclusive/i })
    await user.click(activateButton)

    // Wait for success modal — ExclusiveActivatedModal shows "Exclusive Activated"
    await waitFor(
      () => {
        expect(screen.getByText('Exclusive Activated')).toBeInTheDocument()
      },
      { timeout: 3000 },
    )

    expect(screen.getByText(/Active while you're charging/i)).toBeInTheDocument()

    // Click "Start Walking" button
    const startWalkingButton = screen.getByRole('button', { name: /Start Walking/i })
    await user.click(startWalkingButton)

    // Modal should be closed
    await waitFor(
      () => {
        expect(screen.queryByText('Exclusive Activated')).not.toBeInTheDocument()
      },
      { timeout: 3000 },
    )
  })
})
