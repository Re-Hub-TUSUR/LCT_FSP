import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { ASSIGNMENT_STATUS_LABELS, assignmentQueries } from '@/entities/assessment'
import type { AssignmentDto } from '@/entities/assessment'
import { AssignmentActions } from '@/features/take-assignment'
import { paths } from '@/shared/config'
import { formatDate } from '@/shared/lib'
import { QueryState, Section, Tag } from '@/shared/ui'
import './assignment-inbox.css'

function outcome(item: AssignmentDto): string | null {
  switch (item.status) {
    case 'sent':
      return `Начать можно до ${formatDate(item.dueAt)}`
    case 'in_progress':
      return 'Тест начат'
    case 'review':
      return 'Ответы отправлены: компания проверяет открытые вопросы'
    case 'done':
      return item.score === null
        ? null
        : `Результат: ${Math.round(item.score)} из 100 · проходной балл ${item.passScore}`
    case 'declined':
    case 'expired':
      return null
  }
}

/** Candidate's side of «тестовые»: tests companies sent after a match. Hidden while empty. */
export function AssignmentInbox() {
  const inbox = useQuery(assignmentQueries.incoming())
  if (inbox.isSuccess && inbox.data.length === 0) return null

  return (
    <Section title="Тестовые от компаний">
      <QueryState query={inbox}>
        {(items) => (
          <ul className="inbox">
            {items.map((item) => (
              <li key={item.id} className="inbox__item">
                <div className="inbox__head">
                  <div>
                    <p className="inbox__eyebrow">
                      <Link to={paths.company(item.company.id)}>{item.company.name}</Link>
                      {item.vacancy && ` · ${item.vacancy.name}`}
                    </p>
                    <h3 className="inbox__title">{item.title}</h3>
                  </div>
                  <Tag>{ASSIGNMENT_STATUS_LABELS[item.status]}</Tag>
                </div>
                <p className="inbox__facts">
                  {item.durationMinutes} минут · заданий: {item.tasksCount}
                  {outcome(item) && ` · ${outcome(item)}`}
                </p>
                {item.message && <p className="inbox__message">{item.message}</p>}
                {item.status === 'sent' && <AssignmentActions assignment={item} />}
              </li>
            ))}
          </ul>
        )}
      </QueryState>
    </Section>
  )
}
