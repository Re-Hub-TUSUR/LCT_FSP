import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { Navigate, useLocation } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import { companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { ErrorState, Loader, Splash } from '@/shared/ui'

export type CabinetSetup =
  | { phase: 'open' }
  | { phase: 'loading' }
  | { phase: 'error'; message: string; retry: () => void }
  | { phase: 'required'; setupPath: string }

/** Resume or company profile must exist before the rest of the product opens. */
export function useCabinetSetup(): CabinetSetup {
  const { user } = useSession()
  const role = user?.role
  const candidate = useQuery({
    ...candidateQueries.mine(),
    enabled: role === 'candidate',
  })
  const company = useQuery({
    ...companyQueries.mine(),
    enabled: role === 'employer',
  })

  if (!user || role === 'admin') return { phase: 'open' }

  const query = role === 'candidate' ? candidate : company
  const setupPath = role === 'candidate' ? ROUTES.profileResume : ROUTES.profileCompany

  if (query.isPending) return { phase: 'loading' }
  if (query.isSuccess) return query.data ? { phase: 'open' } : { phase: 'required', setupPath }
  return {
    phase: 'error',
    message: getErrorMessage(query.error),
    retry: () => {
      void query.refetch()
    },
  }
}

export function CabinetGate({ children }: { children: ReactNode }) {
  const location = useLocation()
  const setup = useCabinetSetup()

  if (setup.phase === 'loading') {
    // On a cold start the splash is still up and covers this; later the loader shows on its own.
    return (
      <>
        <Splash />
        <Loader />
      </>
    )
  }
  if (setup.phase === 'error') {
    return <ErrorState message={setup.message} onRetry={setup.retry} />
  }
  if (setup.phase === 'required' && location.pathname !== setup.setupPath) {
    return <Navigate to={setup.setupPath} replace />
  }
  return children
}
