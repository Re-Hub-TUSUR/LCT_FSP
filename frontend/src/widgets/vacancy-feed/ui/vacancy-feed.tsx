import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import {
  DECISION_VIEW_LABELS,
  DECISION_VIEWS,
  parseListView,
  VacancyMatchCard,
  vacancyQueries,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import type { ListView, WorkFormat } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { Chip, EmptyState, FeedSkeleton, Notice, Pagination, QueryState } from '@/shared/ui'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

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
  const view = parseListView(params.get('view'))
  const formats = params.getAll('workFormat') as WorkFormat[]
  const salaryMin = Number(params.get('salaryMin')) || undefined

  const query = useQuery({
    ...vacancyQueries.feed({ page, perPage, view, workFormat: formats, salaryMin }),
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

  const toggleFormat = (format: WorkFormat) =>
    update({
      workFormat: formats.includes(format)
        ? formats.filter((item) => item !== format)
        : [...formats, format],
    })

  return (
    <div className="feed">
      <aside className="feed__filters" aria-label="Фильтры ленты">
        <div className="feed__group">
          <p className="feed__label">Показать</p>
          <div className="feed__chips">
            <Chip active={view === 'all'} onClick={() => update({ view: null })}>
              Подходящие
            </Chip>
            {DECISION_VIEWS.map((item) => (
              <Chip key={item} active={view === item} onClick={() => update({ view: item })}>
                {DECISION_VIEW_LABELS[item]}
              </Chip>
            ))}
          </div>
        </div>
        <div className="feed__group">
          <p className="feed__label">Формат</p>
          <div className="feed__chips">
            {WORK_FORMATS.map((format) => (
              <Chip
                key={format}
                active={formats.includes(format)}
                onClick={() => toggleFormat(format)}
              >
                {WORK_FORMAT_LABELS[format]}
              </Chip>
            ))}
          </div>
        </div>
        <label className="feed__group">
          <span className="feed__label">Зарплата от, ₽</span>
          <input
            className="feed__input"
            inputMode="numeric"
            placeholder="Например, 200 000"
            defaultValue={salaryMin ?? ''}
            onBlur={(e) => update({ salaryMin: e.target.value.replace(/\D/g, '') || null })}
          />
        </label>

        {data?.basis && (
          <div className="feed__basis">
            <p className="feed__label">Лента подобрана по профилю</p>
            {data.basis.category && <p className="feed__basis-main">{data.basis.category.label}</p>}
            <p className="feed__basis-text">
              {data.basis.gradeVerified ? 'Грейд подтверждён тестом' : 'Грейд без теста'}
              {data.basis.salaryExpectation !== null &&
                ` · от ${rub.format(data.basis.salaryExpectation)} ₽`}
            </p>
            <p className="feed__basis-text">{data.basis.stack.join(' · ')}</p>
          </div>
        )}
      </aside>

      <section className="feed__results" aria-label="Вакансии">
        {data && !data.personalized && (
          <Notice>Пройдите тест — лента станет персональной. Пока показаны новые вакансии.</Notice>
        )}
        {data ? (
          data.items.length === 0 ? (
            <EmptyState title={EMPTY[view].title}>{EMPTY[view].text}</EmptyState>
          ) : (
            <>
              <ol className="feed__list">
                {data.items.map((match) => (
                  <li key={match.vacancy.id}>
                    <VacancyMatchCard
                      match={match}
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
