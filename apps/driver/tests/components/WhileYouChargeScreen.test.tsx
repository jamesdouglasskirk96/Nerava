import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WhileYouChargeScreen } from '../../src/components/WhileYouCharge/WhileYouChargeScreen'
import { CaptureIntentResponse } from '../../src/types'
import { ApiError } from '../../src/services/api'

// Mock geolocation
const mockGeolocation = {
  getCurrentPosition: vi.fn(),
}

// @ts-ignore
global.navigator.geolocation = mockGeolocation

// Mock fetch
global.fetch = vi.fn()

describe('WhileYouChargeScreen', () => {
  let queryClient: QueryClient

  beforeEach(() => {
    queryClient = new QueryClient({
      defaultOptions: {
        queries: { retry: false },
      },
    })
    vi.clearAllMocks()
  })

  it('renders featured merchant from mocked API response', async () => {
    // Mock successful geolocation
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 30.2672,
          longitude: -97.7431,
          accuracy: 50,
        },
      })
    })

    // Mock API response
    const mockResponse: CaptureIntentResponse = {
      session_id: 'test-session-123',
      confidence_tier: 'A',
      merchants: [
        {
          place_id: 'mock_asadas_grill',
          name: 'Asadas Grill',
          lat: 30.2680,
          lng: -97.7435,
          distance_m: 150,
          types: ['restaurant'],
          badges: ['Happy Hour ⭐️'],
        },
        {
          place_id: 'mock_eggman_atx',
          name: 'Eggman ATX',
          lat: 30.2665,
          lng: -97.7425,
          distance_m: 200,
          types: ['cafe'],
        },
      ],
      next_actions: {
        request_wallet_pass: false,
        require_vehicle_onboarding: false,
      },
    }

    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      json: async () => mockResponse,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    // Wait for API call and rendering
    await waitFor(() => {
      expect(screen.getByText("You're Charging.")).toBeInTheDocument()
    })

    // Check featured merchant is rendered
    await waitFor(() => {
      expect(screen.getByText('Asadas Grill')).toBeInTheDocument()
      expect(screen.getByText('Happy Hour ⭐️')).toBeInTheDocument()
    })
  })

  it('shows fallback message when geolocation is denied', async () => {
    // Mock geolocation error
    mockGeolocation.getCurrentPosition.mockImplementation((_, error) => {
      error({
        code: 1,
        message: 'User denied geolocation',
      })
    })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    await waitFor(() => {
      expect(screen.getByText(/Location Access Required/i)).toBeInTheDocument()
      expect(screen.getByText(/User denied geolocation/i)).toBeInTheDocument()
    })
  })

  it('renders error state on 401 and shows Sign-in button', async () => {
    // Mock successful geolocation
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 30.2672,
          longitude: -97.7431,
          accuracy: 50,
        },
      })
    })

    // Mock fetch to return 401
    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: false,
      status: 401,
      json: async () => ({ error: 'unauthorized', message: 'Sign in required' }),
    })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    // Assert "Sign in Required" text and button appear
    await waitFor(() => {
      expect(screen.getByText(/Sign in Required/i)).toBeInTheDocument()
      expect(screen.getByText(/Please sign in to see nearby merchants/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Continue with Google/i })).toBeInTheDocument()
    })
  })

  it('renders error state on network failure and shows Retry', async () => {
    // Mock successful geolocation
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 30.2672,
          longitude: -97.7431,
          accuracy: 50,
        },
      })
    })

    // Mock fetch to throw network error
    // @ts-ignore
    global.fetch.mockRejectedValueOnce(new Error('Network error'))

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    // Assert "Can't Load Merchants" text and Retry button appear
    await waitFor(() => {
      expect(screen.getByText(/Can't Load Merchants/i)).toBeInTheDocument()
      expect(screen.getByText(/Network error/i)).toBeInTheDocument()
      expect(screen.getByRole('button', { name: /Retry/i })).toBeInTheDocument()
    })
  })

  it('retry triggers refetch', async () => {
    const user = userEvent.setup()
    
    // Mock successful geolocation
    mockGeolocation.getCurrentPosition.mockImplementation((success) => {
      success({
        coords: {
          latitude: 30.2672,
          longitude: -97.7431,
          accuracy: 50,
        },
      })
    })

    // Mock initial failure, then success
    const mockSuccessResponse: CaptureIntentResponse = {
      session_id: 'test-session-123',
      confidence_tier: 'A',
      merchants: [
        {
          place_id: 'mock_asadas_grill',
          name: 'Asadas Grill',
          lat: 30.2680,
          lng: -97.7435,
          distance_m: 150,
          types: ['restaurant'],
        },
      ],
      next_actions: {
        request_wallet_pass: false,
        require_vehicle_onboarding: false,
      },
    }

    // @ts-ignore
    global.fetch
      .mockRejectedValueOnce(new Error('Network error'))
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockSuccessResponse,
      })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    // Wait for error state
    await waitFor(() => {
      expect(screen.getByText(/Can't Load Merchants/i)).toBeInTheDocument()
    })

    // Click retry button
    const retryButton = screen.getByRole('button', { name: /Retry/i })
    await user.click(retryButton)

    // Assert refetch is called and success state renders
    await waitFor(() => {
      expect(screen.getByText("You're Charging.")).toBeInTheDocument()
      expect(screen.getByText('Asadas Grill')).toBeInTheDocument()
    })
  })
})

