import { useCallback, useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import type { CandidateMatchDto, CandidateSort } from '@/entities/candidate'
import { categoryQueries, GRADE_LABELS, GRADES } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { parseListView, vacancyQueries, WORK_FORMAT_LABELS, WORK_FORMATS } from '@/entities/vacancy'
import type { ListView, WorkFormat } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { plural } from '@/shared/lib'
import { Chip, EmptyState, FeedSkeleton, Pagination, QueryState } from '@/shared/ui'
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

const list = (value: string | null) =>
  (value ?? '')
    .split(',')
    .map((item) => item.trim())
    .filter(Boolean)

/**
 * Recruiter's feed: full-text search (Elasticsearch on the backend) plus deep filters.
 * Inside a category the strongest confirmed profile (test + FSP) goes first.
 */
export function CandidateFeed() {
  const [params, setParams] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)
  const perPage = Number(params.get('perPage')) || 10
  const view = parseListView(params.get('view'))
  const q = params.get('q') ?? ''
  const grades = params.getAll('grade') as Grade[]
  const formats = params.getAll('workFormat') as WorkFormat[]
  const stack = list(params.get('stack'))
  const sort = (params.get('sort') as CandidateSort | null) ?? 'relevance'
  const vacancyId = params.get('vacancyId') ?? undefined
  const [text, setText] = useState(q)
  const [open, setOpen] = useState<CandidateMatchDto | null>(null)
  const [filtersOpen, setFiltersOpen] = useState(false)
  const closePanel = useCallback(() => setOpen(null), [setOpen])

  const dictionary = useQuery(categoryQueries.dictionary())
  const mine = useQuery(vacancyQueries.mine())
  const query = useQuery({
    ...candidateQueries.search({
      page,
      perPage,
      view,
      q: q || undefined,
      specialization: params.get('specialization') ?? undefined,
      grade: grades,
      stack,
      hasFspAchievements: params.get('fsp') === '1' ? true : undefined,
      verifiedOnly: params.get('verified') === '1' || undefined,
      workFormat: formats,
      city: params.get('city') ?? undefined,
      salaryMax: Number(params.get('salaryMax')) || undefined,
      vacancyId,
      sort,
    }),
    placeholderData: keepPreviousData,
  })
  const data = query.data

  const update = (patch: Record<string, string | string[] | null>) => {
    const next = new URLSearchParams(params)
    for (const [key, value] of Object.entries(patch)) {
      next.delete(key)
      if (Array.isArray(value)) value.forEach((item) => next.append(key, item))
      else if (value) next.set(key, value)
    }
    if (!('page' in patch)) next.delete('page')
    setParams(next, { replace: true })
  }

  const toggle = <T extends string>(key: string, values: T[], value: T) =>
    update({
      [key]: values.includes(value) ? values.filter((v) => v !== value) : [...values, value],
    })

  // What the «Фильтры» button reports on a narrow screen.
  const active =
    ['specialization', 'stack', 'city', 'salaryMax', 'vacancyId', 'verified', 'fsp'].filter((key) =>
      params.get(key),
    ).length +
    grades.length +
    formats.length

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
        <h2 className="feed__title">Фильтры</h2>
        <label className="feed__group">
          <span className="feed__label">Подбор под вакансию</span>
          <select
            className="feed__select"
            value={vacancyId ?? ''}
            onChange={(e) => update({ vacancyId: e.target.value || null })}
          >
            <option value="">Без вакансии — по силе профиля</option>
            {mine.data?.items.map((vacancy) => (
              <option key={vacancy.id} value={vacancy.id}>
                {vacancy.title}
                {vacancy.publishedAt ? '' : ' (черновик)'}
              </option>
            ))}
          </select>
        </label>

        <label className="feed__group">
          <span className="feed__label">Специализация</span>
          <select
            className="feed__select"
            value={params.get('specialization') ?? ''}
            onChange={(e) => update({ specialization: e.target.value || null })}
          >
            <option value="">Все специализации</option>
            {dictionary.data?.specializations.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </select>
        </label>

        <div className="feed__group">
          <p className="feed__label">Грейд</p>
          <div className="feed__chips">
            {GRADES.map((grade) => (
              <Chip
                key={grade}
                active={grades.includes(grade)}
                onClick={() => toggle('grade', grades, grade)}
              >
                {GRADE_LABELS[grade]}
              </Chip>
            ))}
          </div>
        </div>

        <label className="feed__group">
          <span className="feed__label">Стек (все через запятую)</span>
          <input
            className="feed__input"
            placeholder="Python, Kafka"
            defaultValue={stack.join(', ')}
            onBlur={(e) => update({ stack: list(e.target.value).join(',') || null })}
          />
        </label>

        <div className="feed__group">
          <p className="feed__label">Подтверждение</p>
          <label className="feed__toggle">
            <input
              type="checkbox"
              checked={params.get('verified') === '1'}
              onChange={(e) => update({ verified: e.target.checked ? '1' : null })}
            />
            Грейд подтверждён тестом
          </label>
          <label className="feed__toggle">
            <input
              type="checkbox"
              checked={params.get('fsp') === '1'}
              onChange={(e) => update({ fsp: e.target.checked ? '1' : null })}
            />
            Есть результаты ФСП
          </label>
        </div>

        <div className="feed__group">
          <p className="feed__label">Формат</p>
          <div className="feed__chips">
            {WORK_FORMATS.map((format) => (
              <Chip
                key={format}
                active={formats.includes(format)}
                onClick={() => toggle('workFormat', formats, format)}
              >
                {WORK_FORMAT_LABELS[format]}
              </Chip>
            ))}
          </div>
        </div>

        <label className="feed__group">
          <span className="feed__label">Город (+ готовые к переезду)</span>
          <input
            className="feed__input"
            placeholder="Москва"
            defaultValue={params.get('city') ?? ''}
            onBlur={(e) => update({ city: e.target.value.trim() || null })}
          />
        </label>

        <label className="feed__group">
          <span className="feed__label">Бюджет до, ₽</span>
          <input
            className="feed__input"
            inputMode="numeric"
            placeholder="300 000"
            defaultValue={params.get('salaryMax') ?? ''}
            onBlur={(e) => update({ salaryMax: e.target.value.replace(/\D/g, '') || null })}
          />
        </label>

        <button
          type="button"
          className="feed__reset"
          onClick={() => setParams(new URLSearchParams())}
        >
          Сбросить фильтры
        </button>
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
                            vacancyId={vacancyId}
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
              vacancyId={vacancyId}
            />
          }
        />
      )}
    </div>
  )
}
