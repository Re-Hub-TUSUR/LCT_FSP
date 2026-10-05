import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { useSession } from '@/entities/session'
import type { UserRole } from '@/entities/user'
import { ROUTES } from '@/shared/config'
import { ErrorState } from '@/shared/ui'

type Props = {
  children: ReactNode
  /** When set, only these roles may open the route. */
  roles?: readonly UserRole[]
}

/**
 * Client-side guard for UX only — every protected endpoint is authorised on the backend as well.
 */
export function RequireAuth({ children, roles }: Props) {
  const { user } = useSession()
  const location = useLocation()

  if (!user) {
    const redirect = encodeURIComponent(`${location.pathname}${location.search}`)
    return <Navigate to={`${ROUTES.auth}?redirect=${redirect}`} replace />
  }

  if (roles && !roles.includes(user.role)) {
    return <ErrorState title="Нет доступа" message="Этот раздел недоступен для вашей роли." />
  }

  return <>{children}</>
}
