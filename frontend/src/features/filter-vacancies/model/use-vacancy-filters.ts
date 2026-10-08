import { useQuery } from '@tanstack/react-query'
import { useCallback, useEffect, useMemo } from 'react'
import { useSearchParams } from 'react-router'
import { parseListView, vacancyQueries } from '@/entities/vacancy'
import type { FeedMode, VacancyFiltersDto } from '@/entities/vacancy'
import { activeCount, filterParams, readFilters, writeFilters } from './filters'

/** The candidate's feed state: the URL is the only source, so a link reopens the same feed. */
export function useVacancyFilters() {
  const [params, setParams] = useSearchParams()
  const filters = useMemo(() => readFilters(params), [params])
  const modeParam = params.get('mode')
  const mode: FeedMode = modeParam === 'free' ? 'free' : 'profile'

  /**
   * New filters. `mode` switches between the profile match and the free search, `saved` names
   * the saved search the feed was opened from (null drops it, leaving out keeps it).
   */
  const setFilters = useCallback(
    (next: VacancyFiltersDto, options: { mode?: FeedMode; saved?: string | null } = {}) =>
      setParams(
        (current) => {
          const updated = writeFilters(current, next, options.mode)
          if ('saved' in options) {
            updated.delete('saved')
            if (options.saved) updated.set('saved', options.saved)
          }
          return updated
        },
        { replace: true },
      ),
    [setParams],
  )

  /** The saved search the feed now shows, or none; the filters stay as they are. */
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

  return {
    filters,
    mode,
    savedId: params.get('saved'),
    view: parseListView(params.get('view')),
    active: activeCount(filters),
    // Without a mode in the URL the backend matches the profile.
    query: { ...filterParams(filters), mode: modeParam === null ? undefined : mode },
    setFilters,
    setSaved,
  }
}

/**
 * The first visit to the feed starts from «Подбор по профилю» with what the profile fills in.
 * True once the filters are settled and the feed may load. The lists of own decisions are
 * opened as they are: the profile does not narrow them.
 */
export function useProfilePrefill(): boolean {
  const [params, setParams] = useSearchParams()
  const view = parseListView(params.get('view'))
  const presets = useQuery(vacancyQueries.feedPresets(view))
  const settled = params.has('mode') || view !== 'all'
  const profile = presets.data?.personalized ? (presets.data.profile ?? null) : null

  useEffect(() => {
    if (settled || !profile) return
    setParams((current) => writeFilters(current, profile, 'profile'), { replace: true })
  }, [settled, profile, setParams])

  return settled || presets.isError || (presets.isSuccess && !profile)
}
