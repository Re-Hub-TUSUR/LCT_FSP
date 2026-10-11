import { render, screen } from '@testing-library/react'
import { afterEach, expect, it } from 'vitest'
import { bannedStore } from '@/entities/session'
import { App } from './app'

afterEach(() => bannedStore.clear())

it('replaces the app when the account is banned', () => {
  bannedStore.set({ reason: 'Спам приглашениями', supportEmail: 'support@kadry.local' })
  render(<App />)
  const dialog = screen.getByRole('dialog')
  expect(dialog).toHaveTextContent('X_X')
  expect(dialog).toHaveTextContent('Вы были забанены по следующей причине: Спам приглашениями.')
  expect(dialog).toHaveTextContent('support@kadry.local')
  expect(screen.getByRole('link', { name: 'support@kadry.local' })).toHaveAttribute(
    'href',
    'mailto:support@kadry.local',
  )
  expect(screen.queryByRole('navigation')).toBeNull()
})
