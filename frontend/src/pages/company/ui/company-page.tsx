import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { CompanyCard, companyQueries } from '@/entities/company'
import { Page, QueryState } from '@/shared/ui'

/** Public company page. */
export function CompanyPage() {
  const { companyId = '' } = useParams()
  const company = useQuery(companyQueries.detail(companyId))

  return (
    <Page title={company.data?.name ?? 'Компания'}>
      <QueryState query={company}>{(data) => <CompanyCard company={data} />}</QueryState>
    </Page>
  )
}
