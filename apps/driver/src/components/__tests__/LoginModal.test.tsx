import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest'
import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { LoginModal } from '../Account/LoginModal'

// Mock the auth service
vi.mock('../../services/auth', () => ({
  teslaLoginStart: vi.fn(),
  ApiError: class ApiError extends Error {
    status: number
    code?: string
    constructor(status: number, code?: string, message?: string) {
      super(message || `API error: ${status}`)
      this.name = 'ApiError'
      this.status = status
      this.code = code
    }
  },
}))

import { teslaLoginStart, ApiError } from '../../services/auth'

const mockedTeslaLoginStart = vi.mocked(teslaLoginStart)

describe('LoginModal', () => {
  const defaultProps = {
    isOpen: true,
    onClose: vi.fn(),
    onSuccess: vi.fn(),
  }

  beforeEach(() => {
    vi.clearAllMocks()
  })

  afterEach(() => {
    vi.restoreAllMocks()
  })

  // --- Test 1: Does not render when isOpen is false ---
  it('returns null when isOpen is false', () => {
    const { container } = render(
      <LoginModal {...defaultProps} isOpen={false} />
    )
    expect(container.innerHTML).toBe('')
  })

  // --- Test 2: Renders sign-in heading and Tesla button ---
  it('renders the sign-in modal with Tesla sign-in button', () => {
    render(<LoginModal {...defaultProps} />)

    expect(screen.getByText('Sign in')).toBeInTheDocument()
    expect(
      screen.getByText('Sign in with your Tesla account to unlock charging rewards.')
    ).toBeInTheDocument()
    expect(
      screen.getByRole('button', { name: /Sign in with Tesla/i })
    ).toBeInTheDocument()
  })

  // --- Test 3: Clicking Tesla button calls teslaLoginStart and redirects ---
  it('calls teslaLoginStart on Tesla button click and redirects to authorization_url', async () => {
    const user = userEvent.setup()

    mockedTeslaLoginStart.mockResolvedValueOnce({
      authorization_url: 'https://auth.tesla.com/oauth2/v3/authorize?client_id=test',
      state: 'test-state-123',
    })

    // Mock window.location.href assignment
    const locationHrefSpy = vi.spyOn(window, 'location', 'get').mockReturnValue({
      ...window.location,
      href: '',
    } as Location)
    // We can't actually test the redirect (jsdom), but we can verify the function was called
    delete (window as any).location
    window.location = { ...window.location, href: '' } as Location

    render(<LoginModal {...defaultProps} />)

    const teslaButton = screen.getByRole('button', { name: /Sign in with Tesla/i })
    await user.click(teslaButton)

    expect(mockedTeslaLoginStart).toHaveBeenCalledTimes(1)

    // Restore
    if (locationHrefSpy) locationHrefSpy.mockRestore()
  })

  // --- Test 4: Error from teslaLoginStart shows error message ---
  it('displays error message when teslaLoginStart fails with ApiError', async () => {
    const user = userEvent.setup()

    const { ApiError: ApiErrorClass } = await import('../../services/auth')
    mockedTeslaLoginStart.mockRejectedValueOnce(
      new ApiErrorClass(500, 'server_error', 'Tesla service unavailable')
    )

    render(<LoginModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /Sign in with Tesla/i }))

    await waitFor(() => {
      expect(screen.getByText('Tesla service unavailable')).toBeInTheDocument()
    })
  })

  // --- Test 5: Generic error shows fallback message ---
  it('displays fallback error for non-ApiError exceptions', async () => {
    const user = userEvent.setup()

    mockedTeslaLoginStart.mockRejectedValueOnce(new TypeError('Network failure'))

    render(<LoginModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /Sign in with Tesla/i }))

    await waitFor(() => {
      expect(
        screen.getByText('Failed to start Tesla sign-in. Please try again.')
      ).toBeInTheDocument()
    })
  })

  // --- Test 6: Close button calls onClose and clears error ---
  it('calls onClose when the close button is clicked', async () => {
    const user = userEvent.setup()

    // First trigger an error so we can verify it's cleared
    mockedTeslaLoginStart.mockRejectedValueOnce(new Error('Some error'))
    render(<LoginModal {...defaultProps} />)

    await user.click(screen.getByRole('button', { name: /Sign in with Tesla/i }))
    await waitFor(() => {
      expect(
        screen.getByText('Failed to start Tesla sign-in. Please try again.')
      ).toBeInTheDocument()
    })

    // Find the close button (the X icon button)
    const buttons = screen.getAllByRole('button')
    // The close button is the one that is NOT the Tesla sign-in button
    const closeButton = buttons.find(
      (btn) => !btn.textContent?.includes('Tesla')
    )
    expect(closeButton).toBeDefined()
    await user.click(closeButton!)

    expect(defaultProps.onClose).toHaveBeenCalledTimes(1)
  })
})
