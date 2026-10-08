import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { ButtonLink, Page } from '@/shared/ui'
import { VacanciesTable } from '@/widgets/vacancies-table'

export function VacanciesPage() {
  const { user } = useSession()
  return (
    <Page
      title="Вакансии"
      lead="Все опубликованные вакансии с обязательной вилкой зарплаты"
      actions={
        user?.role === 'employer' ? (
          <ButtonLink to={ROUTES.vacancyNew}>Добавить вакансию</ButtonLink>
        ) : undefined
      }
    >
      <VacanciesTable />
    </Page>
  )
}
