import { useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router'
import {
  ASSIGNMENT_STATUS_LABELS,
  assignmentApi,
  assignmentKeys,
  assignmentQueries,
} from '@/entities/assessment'
import type { AssignmentDto, AssignmentStatus } from '@/entities/assessment'
import { ReviewPanel } from '@/features/review-assignment'
import { getErrorMessage } from '@/shared/api'
import { ROUTES, paths } from '@/shared/config'
import { formatDate, plural } from '@/shared/lib'
import { Button, ConfirmDialog, EmptyState, QueryState, Sheet } from '@/shared/ui'
import './assignment-review.css'

/** The candidate has not started: the company may still take the test back. */
const REVOCABLE: AssignmentStatus[] = ['sent', 'declined', 'expired']
/** There is finished work to look at. */
const TAKEN: AssignmentStatus[] = ['review', 'done']

/** What needs the employer first: work to grade, then tests in flight, finished ones last. */
const ORDER: AssignmentStatus[] = ['review', 'in_progress', 'sent', 'done', 'declined', 'expired']

/** The date in the «Срок» column and what it means for this status. */
function deadline(item: AssignmentDto): { date: string; note: string } {
  if (item.finishedAt) return { date: item.finishedAt, note: 'сдано' }
  if (item.status === 'expired') return { date: item.dueAt, note: 'срок был' }
  return { date: item.dueAt, note: 'начать до' }
}

const sorted = (items: AssignmentDto[]) =>
  ORDER.flatMap((status) => items.filter((item) => item.status === status))

function Detail({ id }: { id: string }) {
  const detail = useQuery(assignmentQueries.detail(id))
  return (
    <QueryState query={detail} loadingLabel="Загружаем ответы…">
      {(data) => <ReviewPanel key={data.id} detail={data} />}
    </QueryState>
  )
}

/** Employer's side of «тестовые»: what was sent, how it went, and grading of open answers. */
export function AssignmentReview() {
  const queryClient = useQueryClient()
  const sent = useQuery(assignmentQueries.outgoing())
  const [openId, setOpenId] = useState<string | null>(null)
  const [revoking, setRevoking] = useState<AssignmentDto | null>(null)

  const revoke = useMutation({
    mutationFn: (id: string) => assignmentApi.revoke(id),
    onSuccess: () => void queryClient.invalidateQueries({ queryKey: assignmentKeys.outgoing() }),
    onSettled: () => setRevoking(null),
  })
  const opened = sent.data?.find((item) => item.id === openId)
  const waiting = sent.data?.filter((item) => item.status === 'review').length ?? 0

  return (
    <>
      <section className="page-section" aria-labelledby="sent-title">
        <header className="sent__head">
          <h2 id="sent-title" className="page-section__title">
            Отправленные тестовые
          </h2>
          {waiting > 0 && (
            <p className="sent__waiting">
              Ждут проверки <b>{waiting}</b>
            </p>
          )}
        </header>
        <QueryState query={sent}>
          {(items) =>
            items.length === 0 ? (
              <EmptyState title="Вы ещё не отправляли тестовых">
                Откройте профиль кандидата с взаимным интересом в{' '}
                <Link to={ROUTES.feed}>ленте</Link> и отправьте ему тест компании.
              </EmptyState>
            ) : (
              <div className="sent__scroll">
                <table className="sent__table">
                  <thead>
                    <tr>
                      <th scope="col">Кандидат</th>
                      <th scope="col">Тест</th>
                      <th scope="col">Статус</th>
                      <th scope="col">Балл</th>
                      <th scope="col">Срок</th>
                      <th scope="col">Действия</th>
                    </tr>
                  </thead>
                  <tbody>
                    {sorted(items).map((item) => (
                      <tr key={item.id} className={item.id === openId ? 'is-open' : undefined}>
                        <td>
                          <Link to={paths.matchingProfile('candidate', item.candidate.id)}>
                            {item.candidate.name}
                          </Link>
                        </td>
                        <td>
                          {item.title}
                          <span className="sent__hint">
                            {[
                              item.vacancy?.name,
                              `${item.tasksCount} ${plural(item.tasksCount, ['задание', 'задания', 'заданий'])}`,
                            ]
                              .filter(Boolean)
                              .join(' · ')}
                          </span>
                        </td>
                        <td>
                          <span className={`sent__status sent__status--${item.status}`}>
                            {ASSIGNMENT_STATUS_LABELS[item.status]}
                          </span>
                        </td>
                        <td>
                          {item.score === null ? (
                            <span className="sent__score sent__score--none">—</span>
                          ) : (
                            <span
                              className={
                                item.passScore !== null && item.score < item.passScore
                                  ? 'sent__score sent__score--low'
                                  : 'sent__score'
                              }
                            >
                              {Math.round(item.score)}
                            </span>
                          )}
                        </td>
                        <td>
                          {formatDate(deadline(item).date)}
                          <span className="sent__hint">{deadline(item).note}</span>
                        </td>
                        <td className="sent__actions">
                          {TAKEN.includes(item.status) && (
                            <Button
                              variant={item.status === 'review' ? 'solid' : 'ghost'}
                              size="small"
                              onClick={() => setOpenId(item.id === openId ? null : item.id)}
                            >
                              {item.id === openId
                                ? 'Свернуть'
                                : item.status === 'review'
                                  ? 'Проверить'
                                  : 'Ответы'}
                            </Button>
                          )}
                          {REVOCABLE.includes(item.status) && (
                            <Button variant="ghost" size="small" onClick={() => setRevoking(item)}>
                              {item.status === 'sent' ? 'Отозвать' : 'Убрать'}
                            </Button>
                          )}
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )
          }
        </QueryState>
        {revoke.isError && (
          <p className="sent__error" role="alert">
            {getErrorMessage(revoke.error)}
          </p>
        )}
      </section>

      {opened && (
        <Sheet label="Проверка" size="wide" onClose={() => setOpenId(null)}>
          <header className="sent__sheet-head">
            <h2 className="sent__sheet-name">{opened.candidate.name}</h2>
            <p className="sent__sheet-test">
              {[opened.title, opened.vacancy?.name].filter(Boolean).join(' · ')}
            </p>
          </header>
          <Detail id={opened.id} />
        </Sheet>
      )}

      {revoking && (
        <ConfirmDialog
          title={revoking.status === 'sent' ? 'Отозвать тестовое?' : 'Убрать из списка?'}
          confirmLabel={revoke.isPending ? 'Убираем…' : 'Да'}
          busy={revoke.isPending}
          onConfirm={() => revoke.mutate(revoking.id)}
          onCancel={() => setRevoking(null)}
        >
          «{revoking.title}» для {revoking.candidate.name}.
          {revoking.status === 'sent' && ' Кандидат больше не увидит его у себя.'}
        </ConfirmDialog>
      )}
    </>
  )
}
