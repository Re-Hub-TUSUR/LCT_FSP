import { useQuery } from '@tanstack/react-query'
import { assessmentQueries } from '@/entities/assessment'
import { categoryQueries } from '@/entities/category'
import { formatDate } from '@/shared/lib'
import { Page, QueryState, Section, Tag } from '@/shared/ui'

const STEPS = [
  'Опрос по отрасли и специализации',
  'Выбор предполагаемого грейда',
  'Тест на заявленный грейд',
  'Автоматическое присвоение категории',
]

/**
 * Mandatory categorisation path for candidates.
 * TODO(testing): survey → grade choice → attempt runner features; the test generation approach
 * (resistant to leaking tasks) is described in docs/ARCHITECTURE.md.
 */
export function TestingPage() {
  const dictionary = useQuery(categoryQueries.dictionary())
  const status = useQuery(assessmentQueries.status())

  return (
    <Page title="Тестирование" lead="Категория формируется по результатам теста, а не по резюме">
      <Section title="Как это работает">
        <ol>
          {STEPS.map((step) => (
            <li key={step}>{step}</li>
          ))}
        </ol>
      </Section>

      <Section title="Специализации">
        <QueryState query={dictionary}>
          {(data) => (
            <p>
              {data.specializations.map((item) => (
                <Tag key={item.code}>{item.label}</Tag>
              ))}
            </p>
          )}
        </QueryState>
      </Section>

      <Section title="История попыток">
        <QueryState
          query={status}
          isEmpty={(data) => data.history.length === 0}
          emptyTitle="Попыток пока не было"
        >
          {(data) => (
            <ul>
              {data.history.map((attempt) => (
                <li key={attempt.id}>
                  {attempt.specialization} · {attempt.grade} · {formatDate(attempt.startedAt)} ·{' '}
                  {attempt.status}
                </li>
              ))}
            </ul>
          )}
        </QueryState>
      </Section>
    </Page>
  )
}
