import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { CompanyCard, companyQueries } from '@/entities/company'
import { Page, QueryState, Section } from '@/shared/ui'
import { CompanyVacancies } from '@/widgets/vacancies-table'

/** Public company page: the profile and every vacancy the company has published. */
export function CompanyPage() {
  const { companyId = '' } = useParams()
  const company = useQuery(companyQueries.detail(companyId))

  return (
    <Page title={company.data?.name ?? 'Компания'}>
      <QueryState query={company}>
        {(data) => (
          <>
            <CompanyCard company={data} />
            <Section title="Вакансии компании">
              <CompanyVacancies companyId={data.id} />
            </Section>
          </>
        )}
      </QueryState>
    </Page>
  )
}
