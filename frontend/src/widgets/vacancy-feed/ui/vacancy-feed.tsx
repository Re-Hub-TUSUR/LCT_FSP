import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useCallback, useState } from 'react'
import { useSearchParams } from 'react-router'
import { vacancyQueries } from '@/entities/vacancy'
import type { ListView, VacancyMatchDto } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { useProfilePrefill, useVacancyFilters, VacancyFilters } from '@/features/filter-vacancies'
import { EmptyState, FeedSkeleton, Notice, Pagination, QueryState } from '@/shared/ui'
import { VacancyPanel } from './vacancy-panel'
import { VacancyRow } from './vacancy-row'

const EMPTY: Record<ListView, { title: string; text: string }> = {
  all: { title: 'Подходящих вакансий нет', text: 'Ослабьте фильтры или загляните позже.' },
  liked: {
    title: 'Пока ничего не отобрано',
    text: 'Отмечайте вакансии звёздочкой в ленте или свайпом вправо.',
  },
  matched: {
    title: 'Взаимных отметок пока нет',
    text: 'Здесь появятся отобранные вами вакансии, чьи компании отобрали вас.',
  },
  skipped: {
    title: 'Ничего не вырезано',
    text: 'Сюда попадают вакансии, которые вы пропустили. Любую можно вернуть.',
  },
}

/**
 * Candidate's feed: only vacancies relevant to the profile, ranked by fit.
 * No free-text search by design; light filters only. State lives in the URL.
 */
export function VacancyFeed() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const perPage = Number(params.get('perPage')) || 10
  const { view, query: filters, active } = useVacancyFilters()
  const ready = useProfilePrefill()
  const [open, setOpen] = useState<VacancyMatchDto | null>(null)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const closePanel = useCallback(() => setOpen(null), [setOpen])

  const query = useQuery({
    ...vacancyQueries.feed({ ...filters, page, perPage, view }),
    placeholderData: keepPreviousData,
    enabled: ready,
  })
  const data = query.data

  const update = (patch: Record<string, string | null>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(patch)) {
      next.delete(key)
      if (value) next.set(key, value)
    }
    if (!('page' in patch)) next.delete('page')
    setParams(next, { replace: true })
  }

  return (
    <div className="feed">
      <button
        type="button"
        className="feed__filters-toggle"
        aria-expanded={filtersOpen}
        onClick={() => setFiltersOpen((value) => !value)}
      >
        Фильтры
        <span>{filtersOpen ? 'Скрыть' : active > 0 ? `${active} активно` : '+'}</span>
      </button>
      <aside
        className={filtersOpen ? 'feed__filters is-open' : 'feed__filters'}
        aria-label="Фильтры ленты"
      >
        <VacancyFilters />
      </aside>

      <section className="feed__results" aria-label="Вакансии">
        {data && !data.personalized && (
          <Notice>Пройдите тест — лента станет персональной. Пока показаны новые вакансии.</Notice>
        )}
        {data ? (
          data.items.length === 0 ? (
            <div className="feed-table">
              <EmptyState title={EMPTY[view].title}>{EMPTY[view].text}</EmptyState>
            </div>
          ) : (
            <>
              <div className="feed-table">
                <ol className="feed__list">
                  {data.items.map((match) => (
                    <li key={match.vacancy.id}>
                      <VacancyRow
                        match={match}
                        profileStack={data.basis?.stack ?? []}
                        selected={open?.vacancy.id === match.vacancy.id}
                        onOpen={() => setOpen(match)}
                        actions={
                          <ReactionButtons
                            target="vacancy"
                            id={match.vacancy.id}
                            initial={match.reaction}
                          />
                        }
                      />
                    </li>
                  ))}
                </ol>
              </div>
              <Pagination
                page={data.page}
                pages={data.pages}
                perPage={data.perPage}
                total={data.total}
                onPage={(next) => {
                  update({ page: String(next) })
                  window.scrollTo({ top: 0, behavior: 'smooth' })
                }}
                onPerPage={(size) => update({ perPage: String(size) })}
              />
            </>
          )
        ) : query.isPending || !ready ? (
          <FeedSkeleton />
        ) : (
          <QueryState query={query}>{() => null}</QueryState>
        )}
      </section>
      {open && (
        <VacancyPanel
          key={open.vacancy.id}
          match={open}
          profileStack={data?.basis?.stack ?? []}
          onClose={closePanel}
          actions={
            <ReactionButtons
              target="vacancy"
              id={open.vacancy.id}
              initial={
                (data?.items.find((item) => item.vacancy.id === open.vacancy.id) ?? open).reaction
              }
            />
          }
        />
      )}
    </div>
  )
}
