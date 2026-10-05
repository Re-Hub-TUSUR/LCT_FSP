import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'

export type CompanyDto = {
  id: string
  name: string
  industry: string | null
  description: string | null
  website: string | null
  contactEmail: string | null
}

export const companyKeys = {
  all: ['companies'] as const,
  detail: (id: string) => [...companyKeys.all, 'detail', id] as const,
  mine: () => [...companyKeys.all, 'mine'] as const,
}

export const companyQueries = {
  detail: (id: string) =>
    queryOptions({
      queryKey: companyKeys.detail(id),
      queryFn: ({ signal }) => http.get<CompanyDto>(`/companies/${id}`, { signal }),
      enabled: Boolean(id),
    }),
  /** Company profile of the signed-in employer. */
  mine: () =>
    queryOptions({
      queryKey: companyKeys.mine(),
      queryFn: ({ signal }) => http.get<CompanyDto>('/companies/me', { signal }),
    }),
}
