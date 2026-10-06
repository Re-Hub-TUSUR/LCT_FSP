import { useEffect, useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { calendarEventQueries, MEETING_STATUS_LABELS } from '@/entities/calendar-event'
import type { CalendarEventDto, MeetingStatus } from '@/entities/calendar-event'
import { useSession } from '@/entities/session'
import { MeetingDetailsDialog, MeetingFormDialog } from '@/features/manage-meeting'
import { getErrorMessage } from '@/shared/api'
import { addDays, addMonths, startOfDay, startOfWeek } from '@/shared/lib'
import { Button, Chip, ErrorState } from '@/shared/ui'
import { MonthGrid } from './month-grid'
import { WeekGrid } from './week-grid'
import './meeting-calendar.css'

type View = 'week' | 'month'

type Dialog =
  | { kind: 'create'; start: Date; candidateId?: string }
  | { kind: 'details'; event: CalendarEventDto }
  | { kind: 'edit'; event: CalendarEventDto }

const STATUSES: MeetingStatus[] = ['confirmed', 'pending', 'declined']

const rangeFormat = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  year: 'numeric',
})
const monthFormat = new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' })

/** The next full hour within working time, otherwise 10:00 of the next day. */
function nextFreeHour(now: Date): Date {
  const start = new Date(now.getFullYear(), now.getMonth(), now.getDate(), now.getHours() + 1)
  if (start.getHours() >= 9 && start.getHours() <= 18 && start.getDate() === now.getDate()) {
    return start
  }
  return new Date(now.getFullYear(), now.getMonth(), now.getDate() + 1, 10)
}

/** Re-renders once a minute: the «now» line and what counts as the past. */
function useNow() {
  const [now, setNow] = useState(() => new Date())
  useEffect(() => {
    const timer = setInterval(() => setNow(new Date()), 60_000)
    return () => clearInterval(timer)
  }, [])
  return now
}

/**
 * Calendar of interviews. An employer schedules meetings with candidates by clicking a free
 * slot; a candidate sees the meetings they are invited to and confirms or declines them.
 */
export function MeetingCalendar() {
  const { user } = useSession()
  const isEmployer = user?.role === 'employer'
  const [params, setParams] = useSearchParams()
  const now = useNow()
  const [view, setView] = useState<View>('week')
  const [anchor, setAnchor] = useState(() => startOfDay(new Date()))
  // `?candidateId=` comes from a candidate's profile: the form opens with them chosen.
  const [dialog, setDialog] = useState<Dialog | null>(() => {
    const candidateId = params.get('candidateId')
    return isEmployer && candidateId
      ? { kind: 'create', start: nextFreeHour(new Date()), candidateId }
      : null
  })

  const month = addMonths(anchor, 0)
  const from = startOfWeek(view === 'week' ? anchor : month)
  const to = addDays(from, view === 'week' ? 7 : 42)
  const query = useQuery({
    ...calendarEventQueries.range({ from: from.toISOString(), to: to.toISOString() }),
    placeholderData: keepPreviousData,
  })
  const events = query.data ?? []
  const pending = events.filter((e) => e.status === 'pending' && new Date(e.endsAt) > now).length

  const shift = (direction: 1 | -1) =>
    setAnchor((current) =>
      view === 'week' ? addDays(current, 7 * direction) : addMonths(current, direction),
    )
  const closeDialog = () => {
    setDialog(null)
    if (params.has('candidateId')) setParams({}, { replace: true })
  }
  const labelOf = (event: CalendarEventDto) =>
    isEmployer ? event.candidate.name : event.company.name
  const onEvent = (event: CalendarEventDto) => setDialog({ kind: 'details', event })
  const onSlot = isEmployer ? (start: Date) => setDialog({ kind: 'create', start }) : undefined

  return (
    <div className="cal" aria-busy={query.isFetching}>
      <div className="cal__toolbar">
        <div className="cal__nav">
          <button
            type="button"
            className="cal__arrow"
            aria-label={view === 'week' ? 'Предыдущая неделя' : 'Предыдущий месяц'}
            onClick={() => shift(-1)}
          >
            ←
          </button>
          <button
            type="button"
            className="cal__arrow"
            aria-label={view === 'week' ? 'Следующая неделя' : 'Следующий месяц'}
            onClick={() => shift(1)}
          >
            →
          </button>
          <Chip onClick={() => setAnchor(startOfDay(new Date()))}>Сегодня</Chip>
          <h2 className="cal__period" aria-live="polite">
            {view === 'week'
              ? rangeFormat.formatRange(from, addDays(from, 6))
              : monthFormat.format(month)}
          </h2>
        </div>
        <div className="cal__views">
          <Chip active={view === 'week'} onClick={() => setView('week')}>
            Неделя
          </Chip>
          <Chip active={view === 'month'} onClick={() => setView('month')}>
            Месяц
          </Chip>
          {isEmployer && (
            <Button
              size="inline"
              onClick={() => setDialog({ kind: 'create', start: nextFreeHour(now) })}
            >
              Назначить встречу
            </Button>
          )}
        </div>
      </div>

      <div className="cal__summary">
        <p className="cal__hint">
          {isEmployer
            ? 'Нажмите на свободное время в сетке, чтобы назначить встречу кандидату'
            : 'Здесь появляются встречи, на которые вас пригласили компании'}
          {pending > 0 &&
            ` · ${isEmployer ? 'ждут ответа кандидатов' : 'ждут вашего ответа'}: ${pending}`}
        </p>
        <ul className="cal__legend" aria-label="Статусы встреч">
          {STATUSES.map((status) => (
            <li key={status} className={`cal-chip cal-chip--${status}`}>
              {MEETING_STATUS_LABELS[status]}
            </li>
          ))}
        </ul>
      </div>

      {query.isError ? (
        <ErrorState message={getErrorMessage(query.error)} onRetry={() => void query.refetch()} />
      ) : view === 'week' ? (
        <WeekGrid
          weekStart={from}
          events={events}
          now={now}
          labelOf={labelOf}
          onEvent={onEvent}
          onSlot={onSlot}
        />
      ) : (
        <MonthGrid
          month={month}
          events={events}
          now={now}
          labelOf={labelOf}
          onEvent={onEvent}
          onSlot={onSlot}
          onDay={(day) => {
            setAnchor(day)
            setView('week')
          }}
        />
      )}

      {dialog?.kind === 'create' && (
        <MeetingFormDialog
          start={dialog.start}
          candidateId={dialog.candidateId}
          onClose={closeDialog}
        />
      )}
      {dialog?.kind === 'edit' && <MeetingFormDialog event={dialog.event} onClose={closeDialog} />}
      {dialog?.kind === 'details' && (
        <MeetingDetailsDialog
          event={dialog.event}
          role={isEmployer ? 'employer' : 'candidate'}
          onEdit={() => setDialog({ kind: 'edit', event: dialog.event })}
          onClose={closeDialog}
        />
      )}
    </div>
  )
}
