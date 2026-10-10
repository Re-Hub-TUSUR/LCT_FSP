import type { CSSProperties } from 'react'
import type { CalendarEventDto } from '@/entities/calendar-event'
import { addDays, isSameDay } from '@/shared/lib'
import { placeSegments, segmentsOfDay } from '../lib/layout'

/** Height of one hour; the stylesheet reads it as `--hour`. */
const HOUR_PX = 56
const SLOT_MINUTES = 30
// Working hours shown by default; the grid grows to fit earlier or later events.
const FIRST_HOUR = 8
const LAST_HOUR = 20

const weekdayFormat = new Intl.DateTimeFormat('ru-RU', { weekday: 'short' })
const dayLabelFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' })
const timeFormat = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

const isWeekend = (date: Date) => date.getDay() === 0 || date.getDay() === 6

const clock = (minutes: number) =>
  `${String(Math.floor(minutes / 60)).padStart(2, '0')}:${String(minutes % 60).padStart(2, '0')}`

type Props = {
  weekStart: Date
  events: CalendarEventDto[]
  now: Date
  /** Who the meeting is with, from the viewer's side. */
  labelOf: (event: CalendarEventDto) => string
  onEvent: (event: CalendarEventDto) => void
  /** Present for employers: a free slot schedules a meeting at that time. */
  onSlot?: (start: Date) => void
}

/** Seven day columns on a time axis; overlapping meetings share the column width. */
export function WeekGrid({ weekStart, events, now, labelOf, onEvent, onSlot }: Props) {
  const days = Array.from({ length: 7 }, (_, index) => {
    const date = addDays(weekStart, index)
    return { date, segments: placeSegments(segmentsOfDay(events, date)) }
  })
  const all = days.flatMap((day) => day.segments)
  const firstHour = Math.min(FIRST_HOUR, ...all.map((s) => Math.floor(s.start / 60)))
  const lastHour = Math.max(LAST_HOUR, ...all.map((s) => Math.ceil(s.end / 60)))
  const hours = Array.from({ length: lastHour - firstHour }, (_, index) => firstHour + index)
  const slots = hours.flatMap((hour) =>
    Array.from({ length: 60 / SLOT_MINUTES }, (_, index) => hour * 60 + index * SLOT_MINUTES),
  )
  const offset = (minutes: number) => ((minutes - firstHour * 60) / 60) * HOUR_PX
  const nowMinutes = now.getHours() * 60 + now.getMinutes()

  return (
    <div className="cal-week" style={{ '--hour': `${HOUR_PX}px` } as CSSProperties}>
      <div className="cal-week__inner">
        <div className="cal-week__head">
          <span />
          {days.map(({ date }) => (
            <div
              key={date.getTime()}
              className={[
                'cal-week__day',
                isSameDay(date, now) && 'is-today',
                isWeekend(date) && 'is-weekend',
              ]
                .filter(Boolean)
                .join(' ')}
            >
              <span className="cal-week__weekday">{weekdayFormat.format(date)}</span>
              <span className="cal-week__date">{date.getDate()}</span>
            </div>
          ))}
        </div>

        <div className="cal-week__body">
          <div className="cal-week__hours" aria-hidden="true">
            {hours.map((hour) => (
              <span key={hour}>{clock(hour * 60)}</span>
            ))}
          </div>

          {days.map(({ date, segments }) => {
            const today = isSameDay(date, now)
            return (
              <div
                key={date.getTime()}
                className={isWeekend(date) ? 'cal-week__col is-weekend' : 'cal-week__col'}
                role="group"
                aria-label={dayLabelFormat.format(date)}
              >
                {slots.map((minutes) => {
                  const start = new Date(date.getFullYear(), date.getMonth(), date.getDate())
                  start.setMinutes(minutes)
                  const free = Boolean(onSlot) && start > now
                  return (
                    <button
                      key={minutes}
                      type="button"
                      className="cal-slot"
                      // Keyboard users schedule with the toolbar button instead of 150+ tab stops.
                      tabIndex={-1}
                      disabled={!free}
                      data-time={clock(minutes)}
                      aria-label={`Назначить на ${dayLabelFormat.format(date)}, ${clock(minutes)}`}
                      onClick={() => onSlot?.(start)}
                    />
                  )
                })}

                {today && nowMinutes >= firstHour * 60 && nowMinutes <= lastHour * 60 && (
                  <span className="cal-week__now" style={{ top: offset(nowMinutes) }} />
                )}

                {segments.map(({ event, start, end, lane, lanes }) => {
                  const startsAt = new Date(event.startsAt)
                  const endsAt = new Date(event.endsAt)
                  const height = Math.max(offset(end) - offset(start), HOUR_PX / 2)
                  return (
                    <button
                      key={event.id}
                      type="button"
                      className={[
                        'cal-event',
                        `cal-event--${event.status}`,
                        endsAt <= now && 'is-past',
                        // Half an hour has room for one line only: name and time side by side.
                        height < HOUR_PX * 0.75 && 'is-short',
                      ]
                        .filter(Boolean)
                        .join(' ')}
                      style={{
                        top: offset(start),
                        // A gap, so a meeting that starts as the previous one ends doesn't cover it.
                        height: height - 2,
                        left: `${(lane / lanes) * 100}%`,
                        width: `${100 / lanes}%`,
                      }}
                      onClick={() => onEvent(event)}
                    >
                      <span className="cal-event__who">{labelOf(event)}</span>
                      <span className="cal-event__meta">
                        {timeFormat.format(startsAt)} – {timeFormat.format(endsAt)} · {event.title}
                      </span>
                    </button>
                  )
                })}
              </div>
            )
          })}
        </div>
      </div>
    </div>
  )
}
