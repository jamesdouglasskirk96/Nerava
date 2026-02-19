/**
 * MerchantPreview component tests
 *
 * Prerequisites: Add vitest + @testing-library/react to merchant app devDependencies:
 *   npm install -D vitest @testing-library/react @testing-library/jest-dom jsdom
 *
 * Then add to vite.config.ts:
 *   test: { environment: 'jsdom', globals: true }
 *
 * Run with: npx vitest run
 */
import { describe, it, expect, vi, beforeEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import { MemoryRouter } from 'react-router-dom'
import { MerchantPreview } from '../MerchantPreview'

// Mock fetchAPI
vi.mock('../../services/api', () => ({
  fetchAPI: vi.fn(),
  ApiError: class extends Error {
    status: number
    constructor(status: number, code?: string, message?: string) {
      super(message)
      this.status = status
    }
  },
}))

// Mock analytics
vi.mock('../../analytics', () => ({
  capture: vi.fn(),
}))

const mockPreviewData = {
  merchant_id: 'm_test123',
  name: 'Test Coffee Shop',
  address: '123 Main St, Austin TX',
  lat: 30.267,
  lng: -97.743,
  rating: 4.5,
  user_rating_count: 120,
  photo_url: 'https://example.com/photo.jpg',
  photo_urls: [],
  open_now: true,
  business_status: 'OPERATIONAL',
  category: 'coffee',
  nearest_charger: {
    name: 'Tesla Supercharger',
    network: 'Tesla',
    walk_minutes: 3,
    distance_m: 200,
  },
  verified_visit_count: 42,
}

describe('MerchantPreview', () => {
  beforeEach(() => {
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('renders merchant name, address, and rating', async () => {
    const { fetchAPI } = await import('../../services/api')
    ;(fetchAPI as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData)

    render(
      <MemoryRouter initialEntries={['/preview?merchant_id=m_test123&exp=9999999999&sig=abc']}>
        <MerchantPreview />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Test Coffee Shop')).toBeTruthy()
    })
    expect(screen.getByText('123 Main St, Austin TX')).toBeTruthy()
    expect(screen.getByText(/4\.5/)).toBeTruthy()
  })

  it('renders nearest charger card', async () => {
    const { fetchAPI } = await import('../../services/api')
    ;(fetchAPI as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData)

    render(
      <MemoryRouter initialEntries={['/preview?merchant_id=m_test123&exp=9999999999&sig=abc']}>
        <MerchantPreview />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('Tesla Supercharger')).toBeTruthy()
    })
    expect(screen.getByText('3 min')).toBeTruthy()
  })

  it('renders verified visits count', async () => {
    const { fetchAPI } = await import('../../services/api')
    ;(fetchAPI as ReturnType<typeof vi.fn>).mockResolvedValueOnce(mockPreviewData)

    render(
      <MemoryRouter initialEntries={['/preview?merchant_id=m_test123&exp=9999999999&sig=abc']}>
        <MerchantPreview />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('42 verified visits')).toBeTruthy()
    })
  })

  it('shows error for expired link', async () => {
    const { fetchAPI } = await import('../../services/api')
    ;(fetchAPI as ReturnType<typeof vi.fn>).mockRejectedValueOnce(
      new Error('This link has expired')
    )

    render(
      <MemoryRouter initialEntries={['/preview?merchant_id=m_test123&exp=1&sig=old']}>
        <MerchantPreview />
      </MemoryRouter>
    )

    await waitFor(() => {
      expect(screen.getByText('This link has expired.')).toBeTruthy()
    })
  })
})
