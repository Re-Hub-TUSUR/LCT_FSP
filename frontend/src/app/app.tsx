import { createBrowserRouter, RouterProvider } from 'react-router'
import { AppProviders } from './providers/app-providers'
import { routes } from './router/routes'

const router = createBrowserRouter(routes)

export function App() {
  return (
    <AppProviders>
      <RouterProvider router={router} />
    </AppProviders>
  )
}
