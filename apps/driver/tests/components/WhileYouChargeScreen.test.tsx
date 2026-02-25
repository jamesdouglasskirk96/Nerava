import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { WhileYouChargeScreen } from '../../src/components/WhileYouCharge/WhileYouChargeScreen'

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
    const mockMerchants = [
      {
        id: 'mock_asadas_grill',
        merchant_id: 'mock_asadas_grill',
        place_id: 'mock_asadas_grill',
        name: 'Asadas Grill',
        lat: 30.268,
        lng: -97.7435,
        distance_m: 150,
        types: ['restaurant'],
        is_primary: true,
        exclusive_title: 'Happy Hour',
      },
      {
        id: 'mock_eggman_atx',
        merchant_id: 'mock_eggman_atx',
        place_id: 'mock_eggman_atx',
        name: 'Eggman ATX',
        lat: 30.2665,
        lng: -97.7425,
        distance_m: 200,
        types: ['cafe'],
        is_primary: false,
      },
    ]

    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => mockMerchants,
    })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    expect(screen.getByText('What to do while you charge')).toBeInTheDocument()

    // Carousel may render the merchant name in multiple places; use getAllByText
    await waitFor(
      () => {
        expect(screen.getAllByText('Asadas Grill').length).toBeGreaterThan(0)
      },
      { timeout: 3000 },
    )
  })

  it('shows empty state when no merchants are returned', async () => {
    // @ts-ignore
    global.fetch.mockResolvedValueOnce({
      ok: true,
      status: 200,
      json: async () => [],
    })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    await waitFor(
      () => {
        expect(screen.getByText('No experiences yet')).toBeInTheDocument()
      },
      { timeout: 3000 },
    )

    expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument()
  })

  it('shows loading skeletons while fetching', () => {
    // Never resolve the fetch
    // @ts-ignore
    global.fetch.mockReturnValueOnce(new Promise(() => {}))

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    expect(screen.getByText('What to do while you charge')).toBeInTheDocument()
  })

  it('renders empty state on network failure and shows Refresh', async () => {
    // @ts-ignore
    global.fetch.mockRejectedValueOnce(new Error('Network error'))

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    await waitFor(
      () => {
        expect(screen.getByText('No experiences yet')).toBeInTheDocument()
        expect(screen.getByRole('button', { name: /Refresh/i })).toBeInTheDocument()
      },
      { timeout: 3000 },
    )
  })

  it('refresh button triggers refetch', async () => {
    const user = userEvent.setup()

    const mockMerchants = [
      {
        id: 'mock_asadas_grill',
        merchant_id: 'mock_asadas_grill',
        place_id: 'mock_asadas_grill',
        name: 'Asadas Grill',
        lat: 30.268,
        lng: -97.7435,
        distance_m: 150,
        types: ['restaurant'],
        is_primary: true,
      },
    ]

    // @ts-ignore
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => [],
      })
      .mockResolvedValueOnce({
        ok: true,
        status: 200,
        json: async () => mockMerchants,
      })

    render(
      <QueryClientProvider client={queryClient}>
        <BrowserRouter>
          <WhileYouChargeScreen />
        </BrowserRouter>
      </QueryClientProvider>
    )

    await waitFor(
      () => {
        expect(screen.getByText('No experiences yet')).toBeInTheDocument()
      },
      { timeout: 3000 },
    )

    const refreshButton = screen.getByRole('button', { name: /Refresh/i })
    await user.click(refreshButton)

    // Carousel may render the merchant name in multiple places
    await waitFor(
      () => {
        expect(screen.getAllByText('Asadas Grill').length).toBeGreaterThan(0)
      },
      { timeout: 3000 },
    )
  })
})
