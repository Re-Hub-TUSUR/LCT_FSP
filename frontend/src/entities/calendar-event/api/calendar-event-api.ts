import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'

export const CALENDAR_EVENT_KINDS = ['interview', 'assessment', 'task-deadline'] as const

export type CalendarEventKind = (typeof CALENDAR_EVENT_KINDS)[number]

/** The candidate's answer to a meeting the company scheduled. */
export type MeetingStatus = 'pending' | 'confirmed' | 'declined'

/** The other side of an event, or the vacancy it is about. */
export type CalendarPartyDto = {
  id: string
  name: string
}

export type CalendarEventDto = {
  id: string
  title: string
  kind: CalendarEventKind
  startsAt: string
  endsAt: string
  invitationId: string | null
  status: MeetingStatus
  company: CalendarPartyDto
  candidate: CalendarPartyDto
  vacancy: CalendarPartyDto | null
  /** Video call link or office address. */
  location: string | null
  note: string | null
}

export type CalendarRangeParams = {
  from: string
  to: string
}

export type MeetingUpdatePayload = {
  title: string
  startsAt: string
  endsAt: string
  vacancyId: string | null
  location: string | null
  note: string | null
}

export type MeetingCreatePayload = MeetingUpdatePayload & {
  candidateId: string
}

export const calendarEventKeys = {
  all: ['calendar-events'] as const,
  range: (params: CalendarRangeParams) => [...calendarEventKeys.all, 'range', params] as const,
}

export const calendarEventQueries = {
  range: (params: CalendarRangeParams) =>
    queryOptions({
      queryKey: calendarEventKeys.range(params),
      queryFn: ({ signal }) =>
        http.get<CalendarEventDto[]>('/calendar/events', { query: params, signal }),
    }),
}

export const calendarEventApi = {
  /** Employer: a new time resets the candidate's answer to `pending`. */
  schedule: (payload: MeetingCreatePayload) =>
    http.post<CalendarEventDto>('/calendar/events', payload),
  reschedule: (id: string, payload: MeetingUpdatePayload) =>
    http.put<CalendarEventDto>(`/calendar/events/${id}`, payload),
  cancel: (id: string) => http.delete<void>(`/calendar/events/${id}`),
  /** Candidate's answer. */
  respond: (id: string, accept: boolean) =>
    http.post<CalendarEventDto>(`/calendar/events/${id}/${accept ? 'confirm' : 'decline'}`),
}
