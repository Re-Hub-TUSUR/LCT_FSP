import { createBrowserRouter, RouterProvider } from 'react-router'
import { AppProviders } from './providers/app-providers'
import { SessionRestore } from './providers/session-restore'
import { routes } from './router/routes'

const router = createBrowserRouter(routes)

export function App() {
  return (
    <AppProviders>
      <SessionRestore>
        <RouterProvider router={router} />
      </SessionRestore>
    </AppProviders>
  )
}
