import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import { env } from '@/shared/config'

export type CompanyDto = {
  id: string
  name: string
  industry: string | null
  description: string | null
  city: string | null
  size: string | null
  website: string | null
  contactEmail: string | null
  inn: string | null
  ogrn: string | null
  kpp: string | null
  legalAddress: string | null
  hasLogo: boolean
  /** An admin approved the Минцифры registry extract. */
  itAccredited: boolean
}

export type CompanyWrite = {
  name: string
  industry: string
  description: string
  city: string
  size: string | null
  website: string
  contactEmail: string
  inn: string
  ogrn: string | null
  kpp: string | null
  legalAddress: string | null
}

export const companyKeys = {
  all: ['companies'] as const,
  detail: (id: string) => [...companyKeys.all, 'detail', id] as const,
  mine: () => [...companyKeys.all, 'mine'] as const,
  /** The employer's Минцифры extract request. */
  verification: () => [...companyKeys.all, 'verification'] as const,
}

export const companyQueries = {
  detail: (id: string) =>
    queryOptions({
      queryKey: companyKeys.detail(id),
      queryFn: ({ signal }) => http.get<CompanyDto>(`/companies/${id}`, { signal }),
      enabled: Boolean(id),
    }),
  /** Company profile of the signed-in employer; `null` until it is filled in. */
  mine: () =>
    queryOptions({
      queryKey: companyKeys.mine(),
      queryFn: ({ signal }) => http.get<CompanyDto | null>('/companies/me', { signal }),
      staleTime: 30_000,
    }),
}

/** Public, like the company page. `version` busts the browser cache after an upload. */
export function companyLogoUrl(companyId: string, version?: string | number) {
  const url = `${env.apiUrl}/companies/${companyId}/logo`
  return version === undefined ? url : `${url}?v=${version}`
}

export const companyApi = {
  save: (payload: CompanyWrite) => http.put<CompanyDto>('/companies/me', payload),
  uploadLogo: (file: File) => {
    const body = new FormData()
    body.append('file', file)
    return http.post<CompanyDto>('/companies/me/logo', body)
  },
  removeLogo: () => http.delete<CompanyDto>('/companies/me/logo'),
}
