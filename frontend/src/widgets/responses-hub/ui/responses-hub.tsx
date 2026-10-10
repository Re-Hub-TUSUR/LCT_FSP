import type { ReactNode } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { useSession } from '@/entities/session'
import {
  type CandidateInboundDto,
  type EmployerInboundDto,
  responseQueries,
} from '@/entities/response'
import { CandidateMatchCard, candidateQueries } from '@/entities/candidate'
import { SALARY_NOTE, VacancyMatchCard, vacancyQueries } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { InviteCandidateLink } from '@/features/invite-candidate'
import { useRespondToLike } from '@/features/respond-to-like'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { Button, EmptyState, QueryState, Tabs } from '@/shared/ui'
import './responses-hub.css'

type Props = {
  messagesPanel: ReactNode
}

export type ResponsesTab = 'skipped' | 'liked' | 'inbound' | 'messages'

const TAB_LABELS: Record<ResponsesTab, string> = {
  skipped: 'Не понравились',
  liked: 'Мне понравились',
  inbound: 'Я понравился',
  messages: 'Сообщения',
}

const TABS: ResponsesTab[] = ['skipped', 'liked', 'inbound', 'messages']

function parseTab(value: string | null): ResponsesTab {
  return TABS.includes(value as ResponsesTab) ? (value as ResponsesTab) : 'liked'
}

function isCandidateInbound(item: unknown): item is CandidateInboundDto {
  return typeof item === 'object' && item !== null && 'companyId' in item
}

export function ResponsesHub({ messagesPanel }: Props) {
  const { user } = useSession()
  const employer = user?.role === 'employer'
  const [params, setParams] = useSearchParams()
  const tab = parseTab(params.get('tab'))
  const setTab = (next: ResponsesTab) => {
    const copy = new URLSearchParams(params)
    copy.set('tab', next)
    if (next !== 'messages') copy.delete('chat')
    setParams(copy, { replace: true })
  }

  const feedView = tab === 'skipped' || tab === 'liked' ? tab : 'liked'
  const vacancyQuery = useQuery({
    ...vacancyQueries.feed({ page: 1, perPage: 20, view: feedView }),
    enabled: !employer && (tab === 'skipped' || tab === 'liked'),
    placeholderData: keepPreviousData,
  })
  const candidateQuery = useQuery({
    ...candidateQueries.search({ page: 1, perPage: 20, view: feedView }),
    enabled: employer && (tab === 'skipped' || tab === 'liked'),
    placeholderData: keepPreviousData,
  })
  const inboundQuery = useQuery({
    ...responseQueries.inbound(),
    enabled: tab === 'inbound',
    placeholderData: keepPreviousData,
  })

  // Answering leads straight to the conversation instead of a card that silently vanishes.
  const respond = useRespondToLike((chatId) => {
    const next = new URLSearchParams(params)
    next.set('tab', 'messages')
    if (chatId) next.set('chat', chatId)
    setParams(next, { replace: true })
  })

  return (
    <div className="responses">
      <Tabs
        className="responses__tabs"
        label="Мои отклики"
        items={TABS.map((item) => ({ value: item, label: TAB_LABELS[item] }))}
        value={tab}
        onChange={setTab}
      />

      {tab === 'messages' ? (
        messagesPanel
      ) : tab === 'inbound' ? (
        <>
          {respond.isError && (
            <p className="responses__error" role="alert">
              Не удалось ответить: {getErrorMessage(respond.error)}
            </p>
          )}
          <QueryState query={inboundQuery}>
            {(data) =>
              data.length ? (
                <ul className="responses__list">
                  {data.map((item) =>
                    isCandidateInbound(item) ? (
                      <li key={item.companyId} className="responses__card">
                        <div className="responses__card-text">
                          <p className="responses__eyebrow">{item.industry ?? 'Компания'}</p>
                          <h3 className="responses__title">{item.companyName}</h3>
                          {item.vacancyTitle && (
                            <p className="responses__lead">
                              {item.vacancyTitle}
                              {item.salary &&
                                ` · ${formatRubRange(item.salary.from, item.salary.to)} ${SALARY_NOTE}`}
                            </p>
                          )}
                          <p className="responses__time">{formatDateTime(item.reactedAt)}</p>
                        </div>
                        <Button
                          size="inline"
                          disabled={respond.isPending}
                          onClick={() =>
                            respond.mutate({
                              companyId: item.companyId,
                              vacancyId: item.vacancyId ?? undefined,
                            })
                          }
                        >
                          Ответить
                        </Button>
                      </li>
                    ) : (
                      <li
                        key={(item as EmployerInboundDto).candidateId}
                        className="responses__card"
                      >
                        <div className="responses__card-text">
                          <p className="responses__eyebrow">
                            {(item as EmployerInboundDto).vacancyTitle}
                          </p>
                          <h3 className="responses__title">
                            {(item as EmployerInboundDto).displayName}
                          </h3>
                          {(item as EmployerInboundDto).headline ? (
                            <p className="responses__lead">
                              {(item as EmployerInboundDto).headline}
                            </p>
                          ) : null}
                          <p className="responses__time">
                            {formatDateTime((item as EmployerInboundDto).reactedAt)}
                          </p>
                        </div>
                        <Button
                          size="inline"
                          disabled={respond.isPending}
                          onClick={() =>
                            respond.mutate({
                              candidateId: (item as EmployerInboundDto).candidateId,
                              vacancyId: (item as EmployerInboundDto).vacancyId,
                            })
                          }
                        >
                          Ответить
                        </Button>
                      </li>
                    ),
                  )}
                </ul>
              ) : (
                <EmptyState title="Пока пусто">
                  Здесь появятся компании и кандидаты, которым вы понравились, но вы ещё не ответили
                  взаимностью.
                </EmptyState>
              )
            }
          </QueryState>
        </>
      ) : employer ? (
        <QueryState query={candidateQuery} loadingLabel="Загрузка…">
          {(data) =>
            data.items.length ? (
              <ul className="responses__feed">
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
                          />
                          {tab === 'liked' && (
                            <InviteCandidateLink candidateId={match.candidate.id} />
                          )}
                        </>
                      }
                    />
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="Список пуст">
                {tab === 'skipped'
                  ? 'Пропущенные кандидаты появятся здесь после свайпа влево.'
                  : 'Лайкнутые кандидаты появятся после «Интересно» или избранного.'}
              </EmptyState>
            )
          }
        </QueryState>
      ) : (
        <QueryState query={vacancyQuery} loadingLabel="Загрузка…">
          {(data) =>
            data.items.length ? (
              <ul className="responses__feed">
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
              </ul>
            ) : (
              <EmptyState title="Список пуст">
                {tab === 'skipped'
                  ? 'Пропущенные вакансии появятся здесь после свайпа влево.'
                  : 'Понравившиеся вакансии появятся после «Интересно» или избранного.'}
              </EmptyState>
            )
          }
        </QueryState>
      )}
    </div>
  )
}
