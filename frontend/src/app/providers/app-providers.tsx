import { useState } from 'react'
import type { ReactNode } from 'react'
import { QueryClientProvider } from '@tanstack/react-query'
import type { QueryClient } from '@tanstack/react-query'
import { createQueryClient } from '@/shared/api'

type Props = {
  children?: ReactNode
  /** Tests pass an isolated client. */
  queryClient?: QueryClient
}

export function AppProviders({ children, queryClient }: Props) {
  const [client] = useState(() => queryClient ?? createQueryClient())
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}
