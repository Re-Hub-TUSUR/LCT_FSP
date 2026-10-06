import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { refreshSession, useSession } from '@/entities/session'
import { Loader } from '@/shared/ui'

/** Restores the account from the refresh cookie before the landing page decides Войти / Кабинет. */
export function SessionRestore({ children }: { children: ReactNode }) {
  const { user } = useSession()
  const restore = useQuery({
    queryKey: ['session', 'restore'],
    queryFn: () => refreshSession(),
    staleTime: Infinity,
    retry: false,
  })

  if (!user && restore.isPending) return <Loader />
  return children
}
