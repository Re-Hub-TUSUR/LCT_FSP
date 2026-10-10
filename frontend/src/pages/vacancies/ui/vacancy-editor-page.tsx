import { useQuery } from '@tanstack/react-query'
import { Link, useNavigate, useParams } from 'react-router'
import { companyQueries } from '@/entities/company'
import { vacancyQueries } from '@/entities/vacancy'
import { VacancyForm } from '@/features/edit-vacancy'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { EmptyState, ErrorState, Loader, Page } from '@/shared/ui'

const BACK = <Link to={ROUTES.vacancies}>← Вакансии</Link>

/** A new vacancy of the employer's company, or one of its own vacancies opened for editing. */
export function VacancyEditorPage() {
  const { vacancyId } = useParams()
  const navigate = useNavigate()
  const company = useQuery({ ...companyQueries.mine(), retry: false })
  const vacancy = useQuery(vacancyQueries.detail(vacancyId ?? ''))
  const title = vacancyId ? 'Редактирование вакансии' : 'Новая вакансия'

  const body = () => {
    if (company.isPending || (vacancyId && vacancy.isPending)) return <Loader />
    if (company.isError) {
      return (
        <ErrorState
          message={getErrorMessage(company.error)}
          onRetry={() => void company.refetch()}
        />
      )
    }
    if (!company.data) {
      return (
        <EmptyState title="Сначала заполните профиль компании">
          Вакансия публикуется от имени компании.{' '}
          <Link to={ROUTES.profileCompany}>Перейти к профилю компании</Link>
        </EmptyState>
      )
    }
    if (vacancy.isError) {
      return (
        <ErrorState
          message={getErrorMessage(vacancy.error)}
          onRetry={() => void vacancy.refetch()}
        />
      )
    }
    if (vacancy.data && vacancy.data.company.id !== company.data.id) {
      return (
        <EmptyState title="Это вакансия другой компании">
          Править можно только вакансии своей компании.
        </EmptyState>
      )
    }
    return (
      <VacancyForm
        key={vacancy.data?.id ?? 'new'}
        vacancy={vacancy.data ?? null}
        onSaved={() => void navigate(ROUTES.vacancies)}
      />
    )
  }

  return (
    <Page
      title={title}
      eyebrow={BACK}
      lead="Вакансию увидят кандидаты в общей таблице и в своей ленте. Черновик видит только ваша компания."
    >
      {body()}
    </Page>
  )
}
