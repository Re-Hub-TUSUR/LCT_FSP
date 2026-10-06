import type { CalendarEventDto } from '@/entities/calendar-event'
import { addDays } from '@/shared/lib'

/** A piece of an event inside one day, in minutes from that day's midnight. */
export type DaySegment = {
  event: CalendarEventDto
  start: number
  end: number
}

export type PlacedSegment = DaySegment & {
  /** Column among the events that overlap in time, and how many columns that group needs. */
  lane: number
  lanes: number
}

const MINUTE = 60_000

/** The parts of `events` that fall on `day`, clipped to it. */
export function segmentsOfDay(events: CalendarEventDto[], day: Date): DaySegment[] {
  const from = day.getTime()
  const to = addDays(day, 1).getTime()
  const segments: DaySegment[] = []
  for (const event of events) {
    const start = new Date(event.startsAt).getTime()
    const end = new Date(event.endsAt).getTime()
    if (start >= to || end <= from) continue
    segments.push({
      event,
      start: Math.max(0, Math.round((start - from) / MINUTE)),
      end: Math.min(24 * 60, Math.round((end - from) / MINUTE)),
    })
  }
  return segments
}

/** Puts overlapping segments side by side: each group of overlaps shares the width equally. */
export function placeSegments(segments: DaySegment[]): PlacedSegment[] {
  // oxlint-disable-next-line unicorn/no-array-sort -- a copy is sorted; toSorted() needs ES2023
  const sorted = [...segments].sort((a, b) => a.start - b.start || b.end - a.end)
  const placed: PlacedSegment[] = []
  let group: PlacedSegment[] = []
  let groupEnd = -1
  // When the last segment of each lane ends.
  let laneEnds: number[] = []

  const closeGroup = () => {
    for (const segment of group) segment.lanes = laneEnds.length
    group = []
    laneEnds = []
  }

  for (const segment of sorted) {
    if (segment.start >= groupEnd) closeGroup()
    let lane = laneEnds.findIndex((end) => end <= segment.start)
    if (lane === -1) lane = laneEnds.length
    laneEnds[lane] = segment.end
    const item = { ...segment, lane, lanes: 1 }
    group.push(item)
    placed.push(item)
    groupEnd = Math.max(groupEnd, segment.end)
  }
  closeGroup()
  return placed
}
