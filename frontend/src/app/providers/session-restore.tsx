import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { refreshSession, sessionApi, sessionStore, useSession } from '@/entities/session'
import { isAdminHost } from '@/shared/config'
import { Splash } from '@/shared/ui'

/** Restores the account from the refresh cookie before the landing page decides Войти / Кабинет. */
export function SessionRestore({ children }: { children: ReactNode }) {
  const { user } = useSession()
  const restore = useQuery({
    queryKey: ['session', 'restore'],
    queryFn: async () => {
      if (!isAdminHost()) return refreshSession()
      // Do not call refresh here. Its 401 makes the browser ask for the gate password again.
      sessionStore.clear()
      try {
        const token = await sessionApi.adminGate()
        sessionStore.set({ accessToken: token.accessToken, user: token.user })
        return token.accessToken
      } catch {
        return null
      }
    },
    staleTime: Infinity,
    retry: false,
  })

  if (!user && restore.isPending) return <Splash />
  return children
}
