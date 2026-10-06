import type { ReactNode } from 'react'
import type { UseQueryResult } from '@tanstack/react-query'
import { ApiError, getErrorMessage } from '../../api'
import { EmptyState, ErrorState, Loader } from './feedback'

type Props<T> = {
  query: UseQueryResult<T>
  /** Return true when loaded data should be rendered as the empty state. */
  isEmpty?: (data: T) => boolean
  emptyTitle?: string
  /** Replaces the default empty title when the page knows the next step. */
  empty?: ReactNode
  loadingLabel?: string
  children: (data: T) => ReactNode
}

/** Renders loading / error / empty states for a TanStack Query result in a uniform way. */
export function QueryState<T>({
  query,
  isEmpty,
  emptyTitle = 'Пока пусто',
  empty,
  loadingLabel,
  children,
}: Props<T>) {
  if (query.isPending) return <Loader label={loadingLabel} />
  if (query.isError) {
    // A stubbed endpoint is not a failure: nothing to retry, nothing went wrong for the user.
    if (query.error instanceof ApiError && query.error.status === 501) {
      return <EmptyState title="Раздел в разработке">Скоро здесь появятся данные.</EmptyState>
    }
    return (
      <ErrorState message={getErrorMessage(query.error)} onRetry={() => void query.refetch()} />
    )
  }
  if (isEmpty?.(query.data)) {
    if (empty) return <>{empty}</>
    return <EmptyState title={emptyTitle} />
  }
  return <>{children(query.data)}</>
}
