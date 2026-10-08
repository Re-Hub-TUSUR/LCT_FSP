import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getErrorMessage, request } from '@/shared/api'
import { Button, EmptyState, MatchMeter, Notice, Page, QueryState } from '@/shared/ui'
import './ats-page.css'

type Connection = {
  connected: boolean
  provider: string | null
  cursor: string | null
}

type Application = {
  id: string
  candidateName: string
  jobTitle: string
  city: string | null
  score: number | null
  decision: 'pass' | 'reject' | 'review' | null
  reasons: string[]
  matchedSkills: string[]
  missingSkills: string[]
  synced: boolean
}

const DECISION: Record<NonNullable<Application['decision']>, string> = {
  pass: 'Подходит',
  reject: 'Не подходит',
  review: 'На проверку',
}

const DECISION_TONE: Record<NonNullable<Application['decision']>, string> = {
  pass: 'match-card__fact match-card__fact--accent',
  reject: 'match-card__fact match-card__fact--warn',
  review: 'match-card__fact',
}

const connectionKey = ['ats', 'connection'] as const
const applicationsKey = ['ats', 'applications'] as const

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
}

export function AtsPage() {
  const queryClient = useQueryClient()
  const connection = useQuery({
    queryKey: connectionKey,
    queryFn: () => request<Connection>('/ats/connection'),
  })
  const applications = useQuery({
    queryKey: applicationsKey,
    queryFn: () => request<Application[]>('/ats/applications'),
    enabled: connection.data?.connected === true,
  })

  const connect = useMutation({
    mutationFn: () => request<Connection>('/ats/connection', { method: 'POST' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: connectionKey })
    },
  })
  const poll = useMutation({
    mutationFn: () =>
      request<{ ingested: number; screened: number }>('/ats/poll', { method: 'POST' }),
    onSuccess: async () => {
      await queryClient.invalidateQueries({ queryKey: applicationsKey })
      await queryClient.invalidateQueries({ queryKey: connectionKey })
    },
  })

  const link = connection.data
  const error = connect.error ?? poll.error

  return (
    <Page
      title="Внешние отклики"
      lead="Опрос подключённой ATS. Банк кандидатов платформы от этого не меняется."
      actions={
        link ? (
          link.connected ? (
            <Button size="inline" disabled={poll.isPending} onClick={() => poll.mutate()}>
              {poll.isPending ? 'Опрашиваем…' : 'Опросить'}
            </Button>
          ) : (
            <Button size="inline" disabled={connect.isPending} onClick={() => connect.mutate()}>
              {connect.isPending ? 'Подключаем…' : 'Подключить демо'}
            </Button>
          )
        ) : null
      }
    >
      <QueryState query={connection} loadingLabel="Проверяем подключение…">
        {(current) => (
          <div className="ats-page">
            {current.provider ? (
              <p className="ats-page__meta">Провайдер: {current.provider}</p>
            ) : null}
            {error ? <Notice>{getErrorMessage(error)}</Notice> : null}
            {current.connected ? (
              <QueryState query={applications} loadingLabel="Загружаем отклики…">
                {(items) =>
                  items.length === 0 ? (
                    <EmptyState title="Откликов пока нет">Нажмите «Опросить».</EmptyState>
                  ) : (
                    <ul className="ats-list">
                      {items.map((item) => (
                        <li key={item.id}>
                          <ApplicationCard item={item} />
                        </li>
                      ))}
                    </ul>
                  )
                }
              </QueryState>
            ) : null}
          </div>
        )}
      </QueryState>
    </Page>
  )
}

function ApplicationCard({ item }: { item: Application }) {
  const skills = item.matchedSkills.length > 0 || item.missingSkills.length > 0

  return (
    <article className="match-card" aria-label={item.candidateName}>
      <header className="match-card__head">
        <div className="match-card__person">
          <span className="match-card__avatar" aria-hidden="true">
            {initials(item.candidateName)}
          </span>
          <div className="match-card__titles">
            <h3 className="match-card__title">{item.candidateName}</h3>
            <p className="match-card__eyebrow">{item.jobTitle}</p>
          </div>
        </div>
        <div className="match-card__meters">
          <MatchMeter value={item.score === null ? null : item.score / 100} label="Под вакансию" />
        </div>
      </header>

      <ul className="match-card__facts">
        {item.decision ? (
          <li className={DECISION_TONE[item.decision]}>{DECISION[item.decision]}</li>
        ) : null}
        {item.city ? <li className="match-card__fact">{item.city}</li> : null}
      </ul>

      {skills ? (
        <ul className="match-card__stack" aria-label="Навыки">
          {item.matchedSkills.map((skill) => (
            <li key={skill}>{skill}</li>
          ))}
          {item.missingSkills.map((skill) => (
            <li key={skill} className="ats-skill--missing">
              нет {skill}
            </li>
          ))}
        </ul>
      ) : null}

      {item.reasons.length > 0 ? (
        <section className="match-card__why" aria-label="Почему такое решение">
          <p className="match-card__why-title">Почему такое решение</p>
          <ul>
            {item.reasons.map((reason) => (
              <li key={reason}>{reason}</li>
            ))}
          </ul>
        </section>
      ) : null}

      <p className={item.synced ? 'match-card__matched' : 'match-card__eyebrow'}>
        {item.synced ? 'Тег, заметка и оценка записаны в ATS' : 'Обратная запись ещё не прошла'}
      </p>
    </article>
  )
}
