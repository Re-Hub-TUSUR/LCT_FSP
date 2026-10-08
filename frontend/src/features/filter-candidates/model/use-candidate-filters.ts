import { useCallback, useMemo } from 'react'
import { useSearchParams } from 'react-router'
import type { CandidateFiltersDto } from '@/entities/candidate'
import { parseListView } from '@/entities/vacancy'
import { activeCount, filterParams, readFilters, writeFilters } from './filters'

type SearchContext = { vacancyId?: string | null; saved?: string | null; text?: string | null }

const CONTEXT_PARAMS = [
  ['vacancyId', 'vacancyId'],
  ['saved', 'saved'],
  ['text', 'q'],
] as const satisfies readonly (readonly [keyof SearchContext, string])[]

/** The recruiter's search state: the URL is the only source, so a link reopens the same list. */
export function useCandidateFilters() {
  const [params, setParams] = useSearchParams()
  const filters = useMemo(() => readFilters(params), [params])
  const vacancyId = params.get('vacancyId')
  const savedId = params.get('saved')

  /**
   * New filters. `vacancyId` changes the vacancy the search works for, `saved` the saved search
   * it was opened from, `text` the text query; null drops them, leaving out keeps them.
   */
  const setFilters = useCallback(
    (next: CandidateFiltersDto, options: SearchContext = {}) => {
      setParams(
        (current) => {
          const updated = writeFilters(current, next)
          for (const [key, param] of CONTEXT_PARAMS) {
            if (!(key in options)) continue
            updated.delete(param)
            const value = options[key]
            if (value) updated.set(param, value)
          }
          return updated
        },
        { replace: true },
      )
    },
    [setParams],
  )

  /** The saved search the list now shows, or none; the filters stay as they are. */
  const setSaved = useCallback(
    (id: string | null) =>
      setParams(
        (current) => {
          const updated = new URLSearchParams(current)
          updated.delete('saved')
          if (id) updated.set('saved', id)
          return updated
        },
        { replace: true },
      ),
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
    savedId,
    text: params.get('q') ?? '',
    view: parseListView(params.get('view')),
    snapshot: params.toString(),
    active: activeCount(filters),
    query: filterParams(filters),
    setFilters,
    setSaved,
    restore,
  }
}
