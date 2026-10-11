import { screen } from '@testing-library/react'
import { describe, expect, it, vi } from 'vitest'
import { EmailVerification } from '@/features/auth-by-email/ui/email-verification'
import { renderWithProviders } from './test-utils'

describe('email verification', () => {
  it('tells the person to check spam next to the code they were sent', () => {
    renderWithProviders(
      <EmailVerification
        email="dev@fsp.ru"
        onVerified={vi.fn<() => Promise<void>>()}
        onClose={vi.fn<() => void>()}
      />,
    )

    expect(screen.getByText(/код на/)).toBeInTheDocument()
    expect(screen.getByText(/Проверьте папку «Спам»/)).toBeInTheDocument()
  })
})
