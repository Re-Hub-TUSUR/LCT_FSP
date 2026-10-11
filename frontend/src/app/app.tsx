import { useSyncExternalStore } from 'react'
import { createBrowserRouter, RouterProvider } from 'react-router'
import { bannedStore } from '@/entities/session'
import { AppProviders } from './providers/app-providers'
import { SessionRestore } from './providers/session-restore'
import { routes } from './router/routes'
import { BanScreen } from './ui/ban-screen'

const router = createBrowserRouter(routes)

export function App() {
  const ban = useSyncExternalStore(
    bannedStore.subscribe,
    bannedStore.getSnapshot,
    bannedStore.getSnapshot,
  )
  if (ban) return <BanScreen reason={ban.reason} supportEmail={ban.supportEmail} />
  return (
    <AppProviders>
      <SessionRestore>
        <RouterProvider router={router} />
      </SessionRestore>
    </AppProviders>
  )
}
