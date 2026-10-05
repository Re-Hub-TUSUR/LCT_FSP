import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'

export const CALENDAR_EVENT_KINDS = ['interview', 'assessment', 'task-deadline'] as const

export type CalendarEventKind = (typeof CALENDAR_EVENT_KINDS)[number]

export type CalendarEventDto = {
  id: string
  title: string
  kind: CalendarEventKind
  startsAt: string
  endsAt: string
  invitationId: string | null
}

export type CalendarRangeParams = {
  from: string
  to: string
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
