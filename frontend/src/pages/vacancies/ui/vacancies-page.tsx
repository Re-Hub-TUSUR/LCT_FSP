import { useSearchParams } from 'react-router'
import { Page } from '@/shared/ui'
import { VacanciesTable } from '@/widgets/vacancies-table'

const PAGE_SIZE = 20

export function VacanciesPage() {
  const [params] = useSearchParams()
  const page = Math.max(1, Number(params.get('page')) || 1)

  // TODO(vacancies): filters feature (specialization / grade / format) writing to URL search params.
  return (
    <Page title="Вакансии" lead="Все опубликованные вакансии с обязательной вилкой зарплаты">
      <VacanciesTable
        params={{
          search: params.get('q') ?? undefined,
          limit: PAGE_SIZE,
          offset: (page - 1) * PAGE_SIZE,
        }}
      />
    </Page>
  )
}
