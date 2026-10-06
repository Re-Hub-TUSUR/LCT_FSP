import { Link } from 'react-router'
import { ROUTES } from '@/shared/config'
import { Page } from '@/shared/ui'
import { AssessmentBank } from '@/widgets/assessment-bank'

/** Employer's workshop: the company's own tasks and the tests composed from them. */
export function TestBuilderPage() {
  return (
    <Page
      title="Конструктор тестов"
      lead="Задачи компании и тесты, которые вы отправляете кандидатам"
      actions={
        <Link className="feed__link" to={ROUTES.testing}>
          ← Отправленные тестовые
        </Link>
      }
    >
      <AssessmentBank scope="employer" />
    </Page>
  )
}
