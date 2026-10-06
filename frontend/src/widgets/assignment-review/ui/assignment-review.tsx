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
import { formatDate } from '@/shared/lib'
import { Button, ConfirmDialog, EmptyState, QueryState, Section } from '@/shared/ui'
import './assignment-review.css'

/** The candidate has not started: the company may still take the test back. */
const REVOCABLE: AssignmentStatus[] = ['sent', 'declined', 'expired']
/** There is finished work to look at. */
const TAKEN: AssignmentStatus[] = ['review', 'done']

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

  return (
    <>
      <Section title="Отправленные тестовые">
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
                    {items.map((item) => (
                      <tr key={item.id} className={item.id === openId ? 'is-open' : undefined}>
                        <td>
                          <Link to={paths.matchingProfile('candidate', item.candidate.id)}>
                            {item.candidate.name}
                          </Link>
                        </td>
                        <td>
                          {item.title}
                          {item.vacancy && <span className="sent__hint">{item.vacancy.name}</span>}
                        </td>
                        <td>{ASSIGNMENT_STATUS_LABELS[item.status]}</td>
                        <td>{item.score === null ? '—' : Math.round(item.score)}</td>
                        <td>{formatDate(item.finishedAt ?? item.dueAt)}</td>
                        <td className="sent__actions">
                          {TAKEN.includes(item.status) && (
                            <Button
                              variant={item.status === 'review' ? 'solid' : 'ghost'}
                              size="inline"
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
                            <Button variant="ghost" size="inline" onClick={() => setRevoking(item)}>
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
      </Section>

      {opened && (
        <Section title={`${opened.candidate.name} · ${opened.title}`}>
          <Detail id={opened.id} />
        </Section>
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
