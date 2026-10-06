import type { MeetingUpdatePayload } from '@/entities/calendar-event'
import { fromDateTimeInputs } from '@/shared/lib'

/** Minutes → label. An existing meeting of another length adds its own option. */
export const DURATIONS: Record<number, string> = {
  30: '30 минут',
  45: '45 минут',
  60: '1 час',
  90: '1,5 часа',
  120: '2 часа',
}

export const DEFAULT_TITLE = 'Собеседование'

export type MeetingFormValues = {
  title: string
  date: string
  time: string
  duration: string
  vacancyId: string
  location: string
  note: string
}

export type MeetingFormErrors = Partial<Record<keyof MeetingFormValues | 'candidate', string>>

type Result = { ok: true; payload: MeetingUpdatePayload } | { ok: false; errors: MeetingFormErrors }

/** Local date + time + duration → the API payload in UTC. */
export function parseMeetingForm(values: MeetingFormValues, now = new Date()): Result {
  const errors: MeetingFormErrors = {}
  const title = values.title.trim()
  if (!title) errors.title = 'Назовите встречу'

  const startsAt = fromDateTimeInputs(values.date, values.time)
  if (!fromDateTimeInputs(values.date, '00:00')) errors.date = 'Укажите дату'
  else if (!startsAt) errors.time = 'Укажите время'
  else if (startsAt <= now) errors.time = 'Это время уже прошло'

  const minutes = Number(values.duration)
  if (!(minutes > 0)) errors.duration = 'Укажите длительность'

  if (!startsAt || Object.keys(errors).length > 0) return { ok: false, errors }
  return {
    ok: true,
    payload: {
      title,
      startsAt: startsAt.toISOString(),
      endsAt: new Date(startsAt.getTime() + minutes * 60_000).toISOString(),
      vacancyId: values.vacancyId || null,
      location: values.location.trim() || null,
      note: values.note.trim() || null,
    },
  }
}
