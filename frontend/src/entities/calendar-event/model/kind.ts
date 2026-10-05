import type { CalendarEventKind } from '../api/calendar-event-api'

export const CALENDAR_EVENT_KIND_LABELS: Record<CalendarEventKind, string> = {
  interview: 'Собеседование',
  assessment: 'Тестирование',
  'task-deadline': 'Срок задания',
}
