import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate } from 'react-router'
import { responseQueries } from '@/entities/response'
import type { CandidateInboundDto, InboundDto } from '@/entities/response'
import { SALARY_NOTE } from '@/entities/vacancy'
import { useRespondToLike } from '@/features/respond-to-like'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { Button } from '@/shared/ui'
import './company-likes.css'

const isCompanyLike = (item: InboundDto): item is CandidateInboundDto => 'companyId' in item

/**
 * Companies that picked the candidate and wait for an answer: the same likes as «Я понравился»,
 * next to the invitations. Answering makes the interest mutual and opens the chat.
 */
export function CompanyLikes() {
  const navigate = useNavigate()
  const inbound = useQuery(responseQueries.inbound())
  const respond = useRespondToLike((chatId) => {
    const query = new URLSearchParams({ tab: 'messages', ...(chatId && { chat: chatId }) })
    void navigate(`${ROUTES.responses}?${query.toString()}`)
  })
  const likes = (inbound.data ?? []).filter(isCompanyLike)

  if (likes.length === 0) return null

  return (
    <section className="company-likes" aria-labelledby="company-likes-title">
      <h2 id="company-likes-title" className="company-likes__title">
        Вас отобрали компании
        <span className="company-likes__count">{likes.length}</span>
      </h2>
      <p className="company-likes__lead">
        Рекрутер отметил ваш профиль. Ответьте — откроется чат; контакты компания увидит только
        после принятого приглашения.
      </p>
      {respond.isError && (
        <p className="company-likes__error" role="alert">
          Не удалось ответить: {getErrorMessage(respond.error)}
        </p>
      )}
      <ul className="company-likes__list">
        {likes.map((like) => (
          <li key={like.companyId} className="company-likes__item">
            <div className="company-likes__text">
              {like.vacancyTitle && like.vacancyId ? (
                <Link
                  className="company-likes__item-title"
                  to={`${ROUTES.vacancies}?vacancyId=${encodeURIComponent(like.vacancyId)}`}
                >
                  {like.vacancyTitle}
                </Link>
              ) : (
                <p className="company-likes__item-title">{like.vacancyTitle ?? like.companyName}</p>
              )}
              {like.vacancyTitle && (
                <p className="company-likes__item-subtitle">
                  {like.companyName}
                  {like.salary && (
                    <span>
                      {' '}
                      · {formatRubRange(like.salary.from, like.salary.to)} {SALARY_NOTE}
                    </span>
                  )}
                </p>
              )}
              <p className="company-likes__time">{formatDateTime(like.reactedAt)}</p>
            </div>
            <Button
              size="inline"
              disabled={respond.isPending}
              onClick={() =>
                respond.mutate({
                  companyId: like.companyId,
                  vacancyId: like.vacancyId ?? undefined,
                })
              }
            >
              Принять
            </Button>
          </li>
        ))}
      </ul>
    </section>
  )
}
