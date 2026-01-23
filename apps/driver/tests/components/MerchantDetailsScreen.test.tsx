import { describe, it, expect, vi } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { BrowserRouter, MemoryRouter } from 'react-router-dom'
import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { MerchantDetailsScreen } from '../../src/components/MerchantDetails/MerchantDetailsScreen'
import { MerchantDetailsResponse } from '../../src/types'

// Mock fetch
global.fetch = vi.fn()

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
  })

  it('renders merchant details and Add to Wallet triggers modal on success', async () => {
    const user = userEvent.setup()

    // Mock merchant details response
    const mockMerchantDetails: MerchantDetailsResponse = {
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
        badge: 'Happy Hour ⭐️',
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

    // Mock wallet activate response
    const mockWalletActivate = {
      status: 'ok',
      wallet_state: {
        state: 'ACTIVE',
        merchant_id: 'mock_asadas_grill',
        expires_at: new Date(Date.now() + 60 * 60 * 1000).toISOString(),
        active_copy: "This pass is active while you're charging.",
      },
    }

    // @ts-ignore
    global.fetch
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockMerchantDetails,
      })
      .mockResolvedValueOnce({
        ok: true,
        json: async () => mockWalletActivate,
      })

    render(
      <QueryClientProvider client={queryClient}>
        <MemoryRouter initialEntries={['/m/mock_asadas_grill?session_id=test-session']}>
          <MerchantDetailsScreen />
        </MemoryRouter>
      </QueryClientProvider>
    )

    // Wait for merchant details to load
    await waitFor(() => {
      expect(screen.getByText('Asadas Grill')).toBeInTheDocument()
      expect(screen.getByText('Restaurant • Food')).toBeInTheDocument()
    })

    // Click Add to Wallet button
    const addButton = screen.getByRole('button', { name: /Add to Wallet/i })
    await user.click(addButton)

    // Wait for success modal
    await waitFor(() => {
      expect(screen.getByText('Added to Wallet')).toBeInTheDocument()
      expect(screen.getByText(/This pass is active while you're charging/i)).toBeInTheDocument()
    })

    // Click Done button
    const doneButton = screen.getByRole('button', { name: /Done/i })
    await user.click(doneButton)

    // Modal should be closed
    await waitFor(() => {
      expect(screen.queryByText('Added to Wallet')).not.toBeInTheDocument()
    })
  })
})

