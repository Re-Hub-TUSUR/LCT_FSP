import { Navigate, Outlet, useLocation, useNavigation } from 'react-router'
import { isAdminHost, ROUTES } from '@/shared/config'
import { Loader } from '@/shared/ui'

/** Every page is a lazy chunk: while the next one loads, the current screen stays and is dimmed. */
export function RootLayout() {
  const navigation = useNavigation()
  const location = useLocation()
  if (isAdminHost() && location.pathname === '/') return <Navigate to={ROUTES.admin} replace />

  return (
    <>
      {navigation.state === 'loading' && (
        <div className="route-loader">
          <Loader />
        </div>
      )}
      <Outlet />
    </>
  )
}
