import { useState } from 'react'
import type { FormEvent } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { CandidateMatchCard, candidateQueries } from '@/entities/candidate'
import type { CandidateSort } from '@/entities/candidate'
import { categoryQueries, GRADE_LABELS, GRADES } from '@/entities/category'
import type { Grade } from '@/entities/category'
import {
  DECISION_VIEW_LABELS,
  DECISION_VIEWS,
  parseListView,
  vacancyQueries,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import type { ListView, WorkFormat } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { paths } from '@/shared/config'
import { Chip, EmptyState, FeedSkeleton, Pagination, QueryState } from '@/shared/ui'

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

  const onSearch = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    update({ q: text.trim() || null })
  }

  return (
    <div className="feed">
      <aside className="feed__filters" aria-label="Фильтры поиска">
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

        <div className="feed__group">
          <p className="feed__label">Показать</p>
          <div className="feed__chips">
            <Chip active={view === 'all'} onClick={() => update({ view: null })}>
              Все
            </Chip>
            {DECISION_VIEWS.map((item) => (
              <Chip key={item} active={view === item} onClick={() => update({ view: item })}>
                {DECISION_VIEW_LABELS[item]}
              </Chip>
            ))}
          </div>
        </div>

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
          <select
            className="feed__select"
            style={{ width: 'auto' }}
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
          {data && (
            <span className="feed__label">
              Поиск: {data.engine === 'elasticsearch' ? 'Elasticsearch' : 'база данных'}
            </span>
          )}
        </div>

        {data ? (
          data.items.length === 0 ? (
            <EmptyState title={EMPTY[view].title}>{EMPTY[view].text}</EmptyState>
          ) : (
            <>
              <ol className="feed__list">
                {data.items.map((match) => (
                  <li key={match.candidate.id}>
                    <CandidateMatchCard
                      match={match}
                      actions={
                        <>
                          <ReactionButtons
                            target="candidate"
                            id={match.candidate.id}
                            initial={match.reaction}
                            vacancyId={vacancyId}
                          />
                          <Link
                            className="feed__link"
                            to={paths.matchingProfile('candidate', match.candidate.id)}
                          >
                            Профиль и приглашение →
                          </Link>
                        </>
                      }
                    />
                  </li>
                ))}
              </ol>
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
    </div>
  )
}
