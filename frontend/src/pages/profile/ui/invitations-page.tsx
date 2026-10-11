import { Navigate, useLocation } from 'react-router'
import { ROUTES } from '@/shared/config'

/** Old bookmarks and toasts land on the overview, where the list now lives. */
export function InvitationsPage() {
  const { search } = useLocation()
  return <Navigate to={{ pathname: ROUTES.profile, search }} replace />
}
