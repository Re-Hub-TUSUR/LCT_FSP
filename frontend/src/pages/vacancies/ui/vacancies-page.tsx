import { Page } from '@/shared/ui'
import { VacanciesTable } from '@/widgets/vacancies-table'

export function VacanciesPage() {
  return (
    <Page title="Вакансии" lead="Все опубликованные вакансии с обязательной вилкой зарплаты">
      <VacanciesTable />
    </Page>
  )
}
