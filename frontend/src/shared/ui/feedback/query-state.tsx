import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { getErrorMessage } from '../../api'
import { EmptyState, ErrorState, Loader } from './feedback'

type Props<T> = {
  query: UseQueryResult<T>
  /** Return true when loaded data should be rendered as the empty state. */
  isEmpty?: (data: T) => boolean
  emptyTitle?: string
  loadingLabel?: string
  children: (data: T) => ReactNode
}

/** Renders loading / error / empty states for a TanStack Query result in a uniform way. */
export function QueryState<T>({
  query,
  isEmpty,
  emptyTitle = 'Пока пусто',
  loadingLabel,
  children,
}: Props<T>) {
  if (query.isPending) return <Loader label={loadingLabel} />
  if (query.isError) {
    return (
      <ErrorState message={getErrorMessage(query.error)} onRetry={() => void query.refetch()} />
    )
  }
  if (isEmpty?.(query.data)) return <EmptyState title={emptyTitle} />
  return <>{children(query.data)}</>
}
