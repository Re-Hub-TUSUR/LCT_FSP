import { describe, expect, it } from 'vitest'
import { parseMeetingForm } from './form'
import type { MeetingFormValues } from './form'

const NOW = new Date(2026, 9, 6, 12, 0)

const values: MeetingFormValues = {
  title: ' Техническое интервью ',
  date: '2026-10-07',
  time: '11:30',
  duration: '45',
  vacancyId: '',
  location: ' https://meet.example/1 ',
  note: '',
}

describe('parseMeetingForm', () => {
  it('turns local date, time and duration into a UTC range', () => {
    const result = parseMeetingForm(values, NOW)

    expect(result).toEqual({
      ok: true,
      payload: {
        title: 'Техническое интервью',
        startsAt: new Date(2026, 9, 7, 11, 30).toISOString(),
        endsAt: new Date(2026, 9, 7, 12, 15).toISOString(),
        vacancyId: null,
        location: 'https://meet.example/1',
        note: null,
      },
    })
  })

  it('rejects a time that has already passed', () => {
    const result = parseMeetingForm({ ...values, date: '2026-10-06', time: '11:00' }, NOW)

    expect(result).toEqual({ ok: false, errors: { time: 'Это время уже прошло' } })
  })

  it('reports every empty required field', () => {
    const result = parseMeetingForm({ ...values, title: ' ', date: '', duration: '' }, NOW)

    expect(result).toEqual({
      ok: false,
      errors: {
        title: 'Назовите встречу',
        date: 'Укажите дату',
        duration: 'Укажите длительность',
      },
    })
  })
})
