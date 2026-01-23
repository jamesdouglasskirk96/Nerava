import { describe, it, expect, vi } from 'vitest'
import { render, screen } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { WalletSuccessModal } from '../../src/components/WalletSuccess/WalletSuccessModal'

describe('WalletSuccessModal', () => {
  it('renders modal with merchant name and perk title', () => {
    const onClose = vi.fn()

    render(
      <WalletSuccessModal
        merchantName="Asadas Grill"
        perkTitle="Happy Hour"
        onClose={onClose}
      />
    )

    expect(screen.getByText('Added to Wallet')).toBeInTheDocument()
    expect(screen.getByText(/Asadas Grill/i)).toBeInTheDocument()
    expect(screen.getByText(/Happy Hour ⭐️/i)).toBeInTheDocument()
    expect(screen.getByText(/Active while charging/i)).toBeInTheDocument()
  })

  it('calls onClose when Done button is clicked', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(
      <WalletSuccessModal
        merchantName="Asadas Grill"
        perkTitle="Happy Hour"
        onClose={onClose}
      />
    )

    const doneButton = screen.getByRole('button', { name: /Done/i })
    await user.click(doneButton)

    expect(onClose).toHaveBeenCalledTimes(1)
  })

  it('calls onClose when backdrop is clicked', async () => {
    const user = userEvent.setup()
    const onClose = vi.fn()

    render(
      <WalletSuccessModal
        merchantName="Asadas Grill"
        perkTitle="Happy Hour"
        onClose={onClose}
      />
    )

    // Click on backdrop (the outer div)
    const backdrop = screen.getByText('Added to Wallet').closest('.fixed')
    if (backdrop) {
      await user.click(backdrop)
      expect(onClose).toHaveBeenCalledTimes(1)
    }
  })
})

