import type { ReactNode } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { useSession } from '@/entities/session'
import {
  type CandidateInboundDto,
  type EmployerInboundDto,
  responseQueries,
} from '@/entities/response'
import { candidateQueries } from '@/entities/candidate'
import type { CandidateMatchDto } from '@/entities/candidate'
import { SALARY_NOTE, vacancyQueries } from '@/entities/vacancy'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { useRespondToLike } from '@/features/respond-to-like'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { Button, EmptyState, QueryState, Tabs } from '@/shared/ui'
import './responses-hub.css'

export type DecisionTab = 'skipped' | 'liked' | 'matched'

type Props = {
  messagesPanel: ReactNode
  /** The rows of the employer's feed: a candidate looks here as in the feed. */
  renderCandidates: (items: CandidateMatchDto[], tab: DecisionTab) => ReactNode
  /** The rows of the candidate's feed, with the profile stack for the match notes. */
  renderVacancies: (items: VacancyMatchDto[], profileStack: readonly string[]) => ReactNode
}

export type ResponsesTab = 'skipped' | 'liked' | 'matched' | 'inbound' | 'messages'

const TAB_LABELS: Record<ResponsesTab, string> = {
  skipped: 'Не понравились',
  liked: 'Мне понравились',
  matched: 'Взаимно',
  inbound: 'Я понравился',
  messages: 'Сообщения',
}

// «Я понравился» comes before «Взаимно»: an incoming like is answered first, then it is mutual.
const TABS: ResponsesTab[] = ['skipped', 'liked', 'inbound', 'matched', 'messages']

const DECISION_TABS = ['skipped', 'liked', 'matched'] as const

function isDecisionTab(tab: ResponsesTab): tab is (typeof DECISION_TABS)[number] {
  return (DECISION_TABS as readonly string[]).includes(tab)
}

function parseTab(value: string | null): ResponsesTab {
  return TABS.includes(value as ResponsesTab) ? (value as ResponsesTab) : 'liked'
}

function isCandidateInbound(item: unknown): item is CandidateInboundDto {
  return typeof item === 'object' && item !== null && 'companyId' in item
}

export function ResponsesHub({ messagesPanel, renderCandidates, renderVacancies }: Props) {
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

  const feedView = isDecisionTab(tab) ? tab : 'liked'
  const vacancyQuery = useQuery({
    ...vacancyQueries.feed({ page: 1, perPage: 20, view: feedView }),
    enabled: !employer && isDecisionTab(tab),
    placeholderData: keepPreviousData,
  })
  const candidateQuery = useQuery({
    ...candidateQueries.search({ page: 1, perPage: 20, view: feedView }),
    enabled: employer && isDecisionTab(tab),
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
              renderCandidates(data.items, feedView)
            ) : (
              <EmptyState title={tab === 'matched' ? 'Взаимных отметок пока нет' : 'Список пуст'}>
                {tab === 'skipped'
                  ? 'Пропущенные кандидаты появятся здесь после свайпа влево.'
                  : tab === 'matched'
                    ? 'Здесь появятся отобранные вами кандидаты, которые отметили вакансию вашей компании.'
                    : 'Лайкнутые кандидаты появятся после «Интересно» или избранного.'}
              </EmptyState>
            )
          }
        </QueryState>
      ) : (
        <QueryState query={vacancyQuery} loadingLabel="Загрузка…">
          {(data) =>
            data.items.length ? (
              renderVacancies(data.items, data.basis?.stack ?? [])
            ) : (
              <EmptyState title={tab === 'matched' ? 'Взаимных отметок пока нет' : 'Список пуст'}>
                {tab === 'skipped'
                  ? 'Пропущенные вакансии появятся здесь после свайпа влево.'
                  : tab === 'matched'
                    ? 'Здесь появятся вакансии с вашим откликом, чьи компании отобрали вас.'
                    : 'Понравившиеся вакансии появятся после «Интересно» или избранного.'}
              </EmptyState>
            )
          }
        </QueryState>
      )}
    </div>
  )
}
