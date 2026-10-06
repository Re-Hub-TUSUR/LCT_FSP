import type { CalendarEventDto } from '@/entities/calendar-event'
import { addDays, isSameDay, startOfWeek } from '@/shared/lib'
import { segmentsOfDay } from '../lib/layout'

const VISIBLE_EVENTS = 3
const WEEKDAYS = ['пн', 'вт', 'ср', 'чт', 'пт', 'сб', 'вс']

const dayLabelFormat = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long' })
const timeFormat = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

/** 10:00 of the day, or the next full hour when that has already passed today. */
function defaultStart(day: Date, now: Date): Date {
  const start = new Date(day.getFullYear(), day.getMonth(), day.getDate(), 10)
  if (start > now) return start
  return new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours() + 1)
}

type Props = {
  /** First day of the shown month. */
  month: Date
  events: CalendarEventDto[]
  now: Date
  labelOf: (event: CalendarEventDto) => string
  onEvent: (event: CalendarEventDto) => void
  /** Opens the week of the day. */
  onDay: (day: Date) => void
  onSlot?: (start: Date) => void
}

/** Six weeks around the month; a day shows its first meetings and how many more there are. */
export function MonthGrid({ month, events, now, labelOf, onEvent, onDay, onSlot }: Props) {
  const first = startOfWeek(month)
  const days = Array.from({ length: 42 }, (_, index) => addDays(first, index))

  return (
    <div className="cal-month">
      <div className="cal-month__weekdays" aria-hidden="true">
        {WEEKDAYS.map((weekday) => (
          <span key={weekday}>{weekday}</span>
        ))}
      </div>
      <div className="cal-month__grid">
        {days.map((day) => {
          // The API returns events earliest first, so a day's list is already in order.
          const segments = segmentsOfDay(events, day)
          const label = dayLabelFormat.format(day)
          const upcoming = addDays(day, 1) > now
          const classes = [
            'cal-month__cell',
            day.getMonth() !== month.getMonth() && 'is-outside',
            isSameDay(day, now) && 'is-today',
          ]
          return (
            <div key={day.getTime()} className={classes.filter(Boolean).join(' ')}>
              <div className="cal-month__cell-head">
                <button
                  type="button"
                  className="cal-month__date"
                  aria-label={`${label}: открыть неделю`}
                  onClick={() => onDay(day)}
                >
                  {day.getDate()}
                </button>
                {onSlot && upcoming && (
                  <button
                    type="button"
                    className="cal-month__add"
                    aria-label={`Назначить встречу на ${label}`}
                    onClick={() => onSlot(defaultStart(day, now))}
                  >
                    +
                  </button>
                )}
              </div>
              <ul className="cal-month__events">
                {segments.slice(0, VISIBLE_EVENTS).map(({ event }) => (
                  <li key={event.id}>
                    <button
                      type="button"
                      className={`cal-chip cal-chip--${event.status}`}
                      onClick={() => onEvent(event)}
                    >
                      <time dateTime={event.startsAt}>
                        {timeFormat.format(new Date(event.startsAt))}
                      </time>
                      <span>{labelOf(event)}</span>
                    </button>
                  </li>
                ))}
              </ul>
              {segments.length > VISIBLE_EVENTS && (
                <button type="button" className="cal-month__more" onClick={() => onDay(day)}>
                  ещё {segments.length - VISIBLE_EVENTS}
                </button>
              )}
            </div>
          )
        })}
      </div>
    </div>
  )
}
