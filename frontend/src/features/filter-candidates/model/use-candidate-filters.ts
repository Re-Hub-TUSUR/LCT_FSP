import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router'
import type { CandidateFiltersDto } from '@/entities/candidate'
import { parseListView } from '@/entities/vacancy'
import { activeCount, filterParams, readFilters, writeFilters } from './filters'

/** The recruiter's search state: the URL is the only source, so a link reopens the same list. */
export function useCandidateFilters() {
  const [params, setParams] = useSearchParams()
  const filters = useMemo(() => readFilters(params), [params])
  const vacancyId = params.get('vacancyId')

  /** New filters; `vacancyId` changes the vacancy the search works for, null drops it. */
  const setFilters = useCallback(
    (next: CandidateFiltersDto, options: { vacancyId?: string | null } = {}) => {
      setParams(
        (current) => {
          const updated = writeFilters(current, next)
          if ('vacancyId' in options) {
            updated.delete('vacancyId')
            if (options.vacancyId) updated.set('vacancyId', options.vacancyId)
          }
          return updated
        },
        { replace: true },
      )
    },
    [setParams],
  )

  /** Back to a saved state of the URL: the undo of a reset or of a vacancy choice. */
  const restore = useCallback(
    (snapshot: string) => setParams(new URLSearchParams(snapshot), { replace: true }),
    [setParams],
  )

  return {
    filters,
    vacancyId,
    text: params.get('q') ?? '',
    view: parseListView(params.get('view')),
    snapshot: params.toString(),
    active: activeCount(filters),
    query: filterParams(filters),
    setFilters,
    restore,
  }
}
