import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, SalaryRangeDto } from '@/shared/api'
import type { InvitationStatus } from '../model/status'

export type InvitationDto = {
  id: string
  candidateId: string
  company: { id: string; name: string }
  vacancyId: string | null
  message: string
  salary: SalaryRangeDto
  contactMethod: string
  status: InvitationStatus
  createdAt: string
  updatedAt: string
}

export type CreateInvitationPayload = {
  candidateId: string
  vacancyId?: string
  message: string
  salary: SalaryRangeDto
  contactMethod: string
}

export type InvitationDecision = 'accept' | 'decline'

/** `incoming` — addressed to the candidate; `outgoing` — sent by the employer's company. */
export type InvitationDirection = 'incoming' | 'outgoing'

export const invitationKeys = {
  all: ['invitations'] as const,
  list: (direction: InvitationDirection) => [...invitationKeys.all, direction] as const,
}

export const invitationQueries = {
  list: (direction: InvitationDirection) =>
    queryOptions({
      queryKey: invitationKeys.list(direction),
      queryFn: ({ signal }) =>
        http.get<Paginated<InvitationDto>>(`/invitations/${direction}`, { signal }),
    }),
}

/** Plain HTTP calls; mutation lifecycle (invalidation, optimistic updates) lives in features. */
export const invitationApi = {
  create: (payload: CreateInvitationPayload) => http.post<InvitationDto>('/invitations', payload),
  respond: (id: string, decision: InvitationDecision) =>
    http.post<InvitationDto>(`/invitations/${id}/${decision}`),
}
