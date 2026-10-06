import type { CalendarEventKind, MeetingStatus } from '../api/calendar-event-api'

export const CALENDAR_EVENT_KIND_LABELS: Record<CalendarEventKind, string> = {
  interview: 'Собеседование',
  assessment: 'Тестирование',
  'task-deadline': 'Срок задания',
}

export const MEETING_STATUS_LABELS: Record<MeetingStatus, string> = {
  pending: 'Ждёт ответа',
  confirmed: 'Подтверждена',
  declined: 'Отклонена',
}
