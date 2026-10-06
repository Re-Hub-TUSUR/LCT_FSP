import { describe, expect, it } from 'vitest'
import type { CalendarEventDto } from '@/entities/calendar-event'
import { placeSegments, segmentsOfDay } from './layout'

function meeting(id: string, start: Date, minutes: number): CalendarEventDto {
  return {
    id,
    title: id,
    kind: 'interview',
    startsAt: start.toISOString(),
    endsAt: new Date(start.getTime() + minutes * 60_000).toISOString(),
    invitationId: null,
    status: 'pending',
    company: { id: 'c', name: 'ПэйФлоу' },
    candidate: { id: 'p', name: 'Марина Крылова' },
    vacancy: null,
    location: null,
    note: null,
  }
}

const DAY = new Date(2026, 9, 7)
const at = (hours: number, minutes = 0) => new Date(2026, 9, 7, hours, minutes)

describe('segmentsOfDay', () => {
  it('keeps the events of the day and clips the ones crossing midnight', () => {
    const segments = segmentsOfDay(
      [
        meeting('morning', at(10), 60),
        meeting('late', at(23), 120),
        meeting('tomorrow', new Date(2026, 9, 8, 9), 30),
      ],
      DAY,
    )

    expect(segments.map(({ event, start, end }) => [event.id, start, end])).toEqual([
      ['morning', 600, 660],
      ['late', 1380, 1440],
    ])
  })
})

describe('placeSegments', () => {
  it('gives the full width to events that do not overlap', () => {
    const placed = placeSegments(
      segmentsOfDay([meeting('a', at(10), 60), meeting('b', at(11), 60)], DAY),
    )

    expect(placed.map(({ lane, lanes }) => [lane, lanes])).toEqual([
      [0, 1],
      [0, 1],
    ])
  })

  it('splits the width between overlapping events and reuses a freed lane', () => {
    const placed = placeSegments(
      segmentsOfDay(
        [meeting('a', at(10), 90), meeting('b', at(10, 30), 30), meeting('c', at(11), 60)],
        DAY,
      ),
    )

    expect(placed.map(({ event, lane, lanes }) => [event.id, lane, lanes])).toEqual([
      ['a', 0, 2],
      ['b', 1, 2],
      ['c', 1, 2],
    ])
  })
})
