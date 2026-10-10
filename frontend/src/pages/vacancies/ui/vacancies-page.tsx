import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { ButtonLink, Page } from '@/shared/ui'
import { VacanciesTable } from '@/widgets/vacancies-table'

export function VacanciesPage() {
  const { user } = useSession()
  const employer = user?.role === 'employer'
  return (
    <Page
      title="Вакансии"
      lead={
        employer
          ? 'Вакансии вашей компании: опубликованные и черновики'
          : 'Все опубликованные вакансии с обязательной вилкой зарплаты'
      }
      actions={
        employer ? <ButtonLink to={ROUTES.vacancyNew}>Добавить вакансию</ButtonLink> : undefined
      }
    >
      <VacanciesTable />
    </Page>
  )
}
