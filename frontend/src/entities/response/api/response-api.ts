import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'

export type CandidateInboundDto = {
  companyId: string
  companyName: string
  industry: string | null
  vacancyId: string | null
  reactedAt: string
}

export type EmployerInboundDto = {
  candidateId: string
  displayName: string
  headline: string | null
  vacancyId: string
  vacancyTitle: string
  reactedAt: string
}

export type InboundDto = CandidateInboundDto | EmployerInboundDto

export const responseKeys = {
  all: ['responses'] as const,
  inbound: () => [...responseKeys.all, 'inbound'] as const,
}

export const responseQueries = {
  inbound: () =>
    queryOptions({
      queryKey: responseKeys.inbound(),
      queryFn: ({ signal }) => http.get<InboundDto[]>('/responses/inbound', { signal }),
    }),
}

export const responseApi = {
  respondCompany: (companyId: string, vacancyId?: string) =>
    http.post<void>(
      `/responses/inbound/companies/${companyId}/respond`,
      undefined,
      vacancyId ? { query: { vacancyId } } : undefined,
    ),
  respondCandidate: (candidateId: string, vacancyId?: string) =>
    http.post<void>(
      `/responses/inbound/candidates/${candidateId}/respond`,
      undefined,
      vacancyId ? { query: { vacancyId } } : undefined,
    ),
}
