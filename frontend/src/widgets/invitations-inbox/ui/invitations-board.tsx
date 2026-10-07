import { useQuery } from '@tanstack/react-query'
import type { ReactNode } from 'react'
import { useSearchParams } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import { INVITATION_STATUSES, invitationQueries } from '@/entities/invitation'
import type { InvitationDirection, InvitationDto, InvitationStatus } from '@/entities/invitation'
import { SALARY_NOTE } from '@/entities/vacancy'
import { ApiError } from '@/shared/api'
import { RespondButtons } from '@/features/respond-to-invitation'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { ChipList, QueryState, StatusTag } from '@/shared/ui'
import type { StatusTone } from '@/shared/ui'
import './invitations-board.css'

type Filter = 'all' | InvitationStatus

const TONES: Record<InvitationStatus, StatusTone> = {
  sent: 'new',
  viewed: 'wait',
  accepted: 'done',
  declined: 'off',
}

const LABELS: Record<InvitationDirection, Record<InvitationStatus, string>> = {
  incoming: { sent: 'Новое', viewed: 'Просмотрено', accepted: 'Принято', declined: 'Отклонено' },
  outgoing: {
    sent: 'Отправлено',
    viewed: 'Просмотрено',
    accepted: 'Принято',
    declined: 'Отклонено',
  },
}

const FILTER_LABELS: Record<InvitationDirection, Record<Filter, string>> = {
  incoming: {
    all: 'Все',
    sent: 'Новые',
    viewed: 'Просмотренные',
    accepted: 'Принятые',
    declined: 'Отклонённые',
  },
  outgoing: {
    all: 'Все',
    sent: 'Отправленные',
    viewed: 'Просмотренные',
    accepted: 'Принятые',
    declined: 'Отклонённые',
  },
}

const FILTERS: Filter[] = ['all', ...INVITATION_STATUSES]

export const NOT_READY =
  'Приглашения ещё подключаются на сервере: список появится, как только раздел заработает.'

/** The server answers 501 while the invitations endpoints are stubs. */
export function isNotReady(error: unknown): boolean {
  return error instanceof ApiError && error.status === 501
}

function isFilter(value: string | null): value is Filter {
  return value !== null && (FILTERS as string[]).includes(value)
}

export function InvitationStatusTag({
  status,
  direction,
}: {
  status: InvitationStatus
  direction: InvitationDirection
}) {
  return <StatusTag tone={TONES[status]}>{LABELS[direction][status]}</StatusTag>
}

/** The employer sees who was invited; the list stores only the candidate id. */
export function CandidateName({ id, fallback = 'Кандидат' }: { id: string; fallback?: string }) {
  const candidate = useQuery(candidateQueries.detail(id))
  return <>{candidate.data?.displayName ?? fallback}</>
}

/** Filters, the list on the left and the chosen invitation on the right (`?id=` in the URL). */
export function InvitationsBoard({
  direction,
  empty,
}: {
  direction: InvitationDirection
  empty?: ReactNode
}) {
  const query = useQuery(invitationQueries.list(direction))
  const [params, setParams] = useSearchParams()
  const rawFilter = params.get('status')
  const filter: Filter = isFilter(rawFilter) ? rawFilter : 'all'

  const update = (patch: Record<string, string | null>) =>
    setParams(
      (prev) => {
        const next = new URLSearchParams(prev)
        for (const [key, value] of Object.entries(patch)) {
          if (value === null) next.delete(key)
          else next.set(key, value)
        }
        return next
      },
      { replace: true },
    )

  if (isNotReady(query.error)) {
    return <p className="inv-board__empty">{NOT_READY}</p>
  }

  return (
    <QueryState
      query={query}
      isEmpty={(page) => page.items.length === 0}
      emptyTitle={direction === 'incoming' ? 'Приглашений пока нет' : 'Вы ещё никого не пригласили'}
      empty={empty}
    >
      {(page) => {
        const items = page.items
        const list = filter === 'all' ? items : items.filter((item) => item.status === filter)
        const chosen = list.find((item) => item.id === params.get('id')) ?? list[0] ?? null
        return (
          <div className="inv-board">
            <div className="inv-board__filters" role="toolbar" aria-label="Статус приглашения">
              {FILTERS.map((option) => {
                const count =
                  option === 'all'
                    ? items.length
                    : items.filter((item) => item.status === option).length
                return (
                  <button
                    key={option}
                    type="button"
                    className="inv-pill"
                    aria-pressed={filter === option}
                    onClick={() => update({ status: option === 'all' ? null : option, id: null })}
                  >
                    {FILTER_LABELS[direction][option]}
                    <span className="inv-pill__count">{count}</span>
                  </button>
                )
              })}
            </div>

            <div className="inv-board__body">
              {list.length === 0 ? (
                <p className="inv-board__empty">В этом статусе приглашений нет.</p>
              ) : (
                <ul className="inv-board__list" aria-label="Приглашения">
                  {list.map((item) => (
                    <li key={item.id}>
                      <button
                        type="button"
                        className="inv-item"
                        aria-current={chosen?.id === item.id ? 'true' : undefined}
                        onClick={() => update({ id: item.id })}
                      >
                        <span className="inv-item__top">
                          <InvitationStatusTag status={item.status} direction={direction} />
                          <span className="inv-item__time">{formatDateTime(item.createdAt)}</span>
                        </span>
                        <span className="inv-item__who">
                          {direction === 'incoming' ? (
                            item.company.name
                          ) : (
                            <CandidateName id={item.candidateId} />
                          )}
                        </span>
                        <span className="inv-item__salary">
                          {formatRubRange(item.salary.from, item.salary.to)}
                        </span>
                      </button>
                    </li>
                  ))}
                </ul>
              )}
              {chosen ? (
                <InvitationDetail invitation={chosen} direction={direction} />
              ) : (
                <p className="inv-board__empty">
                  Выберите приглашение — подробности откроются здесь.
                </p>
              )}
            </div>
          </div>
        )
      }}
    </QueryState>
  )
}

function InvitationDetail({
  invitation,
  direction,
}: {
  invitation: InvitationDto
  direction: InvitationDirection
}) {
  const { status, company, salary, message, contactMethod, vacancyId, createdAt, updatedAt } =
    invitation
  const answered = status === 'accepted' || status === 'declined'
  const steps = [
    { title: 'Отправлено', done: true, time: formatDateTime(createdAt) },
    { title: 'Просмотрено', done: status !== 'sent', time: null },
    {
      title: status === 'accepted' ? 'Принято' : status === 'declined' ? 'Отклонено' : 'Ответ',
      done: answered,
      time: answered ? formatDateTime(updatedAt) : null,
    },
  ]

  return (
    <article className="inv-detail" aria-label="Приглашение">
      <header className="inv-detail__top">
        <p className="inv-detail__who">
          {direction === 'incoming' ? company.name : <CandidateName id={invitation.candidateId} />}
        </p>
        <InvitationStatusTag status={status} direction={direction} />
      </header>
      <p className="inv-detail__salary">
        {formatRubRange(salary.from, salary.to)} <span>{SALARY_NOTE}</span>
      </p>
      <ChipList items={[vacancyId ? 'По опубликованной вакансии' : 'Без публикации вакансии']} />

      <div className="inv-detail__message">
        <p className="inv-detail__label">
          {direction === 'incoming' ? 'Сообщение от работодателя' : 'Ваше сообщение'}
        </p>
        <p>{message}</p>
      </div>

      <div>
        <p className="inv-detail__label">Способ связи</p>
        <p className="inv-detail__text">{contactMethod}</p>
      </div>

      <ol className="inv-steps" aria-label="Ход приглашения">
        {steps.map((step) => (
          <li
            key={step.title}
            className={step.done ? 'inv-steps__item is-done' : 'inv-steps__item'}
          >
            <b>{step.title}</b>
            {step.time ?? (step.done ? '' : 'Пока нет')}
          </li>
        ))}
      </ol>

      <div className="inv-detail__act">
        {direction === 'incoming' && status === 'accepted' && (
          <p className="inv-detail__text">
            Вы приняли приглашение: работодатель видит ваши контакты. Дальше он свяжется с вами:{' '}
            {contactMethod.toLowerCase()}.
          </p>
        )}
        {direction === 'incoming' && status === 'declined' && (
          <p className="inv-detail__text">
            Вы отклонили приглашение. Ваши контакты остались скрыты.
          </p>
        )}
        {direction === 'incoming' && !answered && (
          <>
            <p className="inv-detail__text">
              Если примете, работодатель увидит ваши email и телефон. До этого контакты скрыты.
            </p>
            <div className="inv-detail__buttons">
              <RespondButtons invitation={invitation} />
            </div>
          </>
        )}
        {direction === 'outgoing' && (
          <p className="inv-detail__text">
            {status === 'accepted'
              ? 'Кандидат принял приглашение — контакты открыты в его профиле.'
              : status === 'declined'
                ? 'Кандидат отклонил приглашение.'
                : 'Контакты кандидата откроются, когда он примет приглашение.'}
          </p>
        )}
      </div>
    </article>
  )
}
