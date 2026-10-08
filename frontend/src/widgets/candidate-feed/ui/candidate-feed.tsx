import { useCallback, useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import type { CandidateMatchDto, CandidateSort } from '@/entities/candidate'
import type { ListView } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { CandidateFilters, useCandidateFilters } from '@/features/filter-candidates'
import { plural } from '@/shared/lib'
import { EmptyState, FeedSkeleton, Pagination, QueryState } from '@/shared/ui'
import { CandidatePanel } from './candidate-panel'
import { CandidateRow } from './candidate-row'

const SORTS: Record<CandidateSort, string> = {
  relevance: 'По релевантности',
  assessment: 'По баллу теста',
  salary: 'По ожиданиям ↑',
  experience: 'По опыту',
}

const EMPTY: Record<ListView, { title: string; text: string }> = {
  all: { title: 'Никого не нашли', text: 'Уберите часть фильтров или переформулируйте запрос.' },
  liked: {
    title: 'Пока никто не отобран',
    text: 'Отмечайте кандидатов звёздочкой или свайпом вправо.',
  },
  matched: {
    title: 'Взаимных отметок пока нет',
    text: 'Здесь появятся отобранные вами кандидаты, которые отметили вакансию вашей компании.',
  },
  skipped: {
    title: 'Никто не вырезан',
    text: 'Сюда попадают кандидаты, которых вы пропустили. Любого можно вернуть.',
  },
}

/**
 * Recruiter's feed: full-text search (Elasticsearch on the backend) plus deep filters.
 * Inside a category the strongest confirmed profile (test + FSP) goes first.
 */
export function CandidateFeed() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const perPage = Number(params.get('perPage')) || 10
  const { view, text: q, vacancyId, query: filters, active } = useCandidateFilters()
  const sort = (params.get('sort') as CandidateSort | null) ?? 'relevance'
  const [text, setText] = useState(q)
  const [open, setOpen] = useState<CandidateMatchDto | null>(null)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const closePanel = useCallback(() => setOpen(null), [setOpen])

  const query = useQuery({
    ...candidateQueries.search({
      ...filters,
      page,
      perPage,
      view,
      q: q || undefined,
      vacancyId: vacancyId ?? undefined,
      sort,
    }),
    placeholderData: keepPreviousData,
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

  const onSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    update({ q: text.trim() || null })
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
        aria-label="Фильтры поиска"
      >
        <CandidateFilters />
      </aside>

      <section className="feed__results" aria-label="Кандидаты">
        <form className="feed__search" role="search" onSubmit={onSearch}>
          <input
            aria-label="Поиск по кандидатам"
            placeholder="Например: сеньор питон kafka или CTF"
            value={text}
            onChange={(e) => setText(e.target.value)}
          />
          <button type="submit">Найти</button>
        </form>

        <div className="feed__toolbar">
          <p className="feed__found">
            {data && (
              <>
                <span className="feed__found-count">{data.total}</span>
                <span className="feed__label">
                  {plural(data.total, ['кандидат', 'кандидата', 'кандидатов'])}
                </span>
                <span className="feed__label">
                  Поиск: {data.engine === 'elasticsearch' ? 'Elasticsearch' : 'база данных'}
                </span>
              </>
            )}
          </p>
          <select
            className="feed__select feed__select--sort"
            aria-label="Сортировка"
            value={sort}
            onChange={(e) =>
              update({ sort: e.target.value === 'relevance' ? null : e.target.value })
            }
          >
            {Object.entries(SORTS).map(([value, label]) => (
              <option key={value} value={value}>
                {label}
              </option>
            ))}
          </select>
        </div>

        {data ? (
          data.items.length === 0 ? (
            <div className="feed-table">
              <EmptyState title={EMPTY[view].title}>{EMPTY[view].text}</EmptyState>
            </div>
          ) : (
            <>
              <div className="feed-table">
                <div className="feed-table__head candidate-row__grid" aria-hidden="true">
                  <span>Кандидат</span>
                  <span>Категория · тест</span>
                  <span>Под вакансию</span>
                  <span>Сила профиля</span>
                  <span>Ожидания</span>
                  <span>Решение</span>
                </div>
                <ol className="feed__list">
                  {data.items.map((match) => (
                    <li key={match.candidate.id}>
                      <CandidateRow
                        match={match}
                        dimmed={match.reaction === 'skip' && view !== 'skipped'}
                        selected={open?.candidate.id === match.candidate.id}
                        onOpen={() => setOpen(match)}
                        actions={
                          <ReactionButtons
                            target="candidate"
                            id={match.candidate.id}
                            initial={match.reaction}
                            vacancyId={vacancyId ?? undefined}
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
        ) : query.isPending ? (
          <FeedSkeleton />
        ) : (
          <QueryState query={query}>{() => null}</QueryState>
        )}
      </section>
      {open && (
        <CandidatePanel
          key={open.candidate.id}
          match={open}
          onClose={closePanel}
          actions={
            <ReactionButtons
              target="candidate"
              id={open.candidate.id}
              initial={open.reaction}
              vacancyId={vacancyId ?? undefined}
            />
          }
        />
      )}
    </div>
  )
}
