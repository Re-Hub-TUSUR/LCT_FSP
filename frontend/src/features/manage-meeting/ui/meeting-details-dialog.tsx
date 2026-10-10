import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { Link } from 'react-router'
import {
  calendarEventApi,
  calendarEventKeys,
  MEETING_STATUS_LABELS,
} from '@/entities/calendar-event'
import type { CalendarEventDto } from '@/entities/calendar-event'
import { getErrorMessage } from '@/shared/api'
import { paths } from '@/shared/config'
import { isHttpUrl } from '@/shared/lib'
import { Button, Modal } from '@/shared/ui'
import './manage-meeting.css'

const dayFormat = new Intl.DateTimeFormat('ru-RU', {
  weekday: 'long',
  day: 'numeric',
  month: 'long',
})
const timeFormat = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })

type Props = {
  event: CalendarEventDto
  /** The employer manages the meeting, the candidate answers it. */
  role: 'employer' | 'candidate'
  onEdit: () => void
  onClose: () => void
}

export function MeetingDetailsDialog({ event, role, onEdit, onClose }: Props) {
  const queryClient = useQueryClient()
  const [confirmingCancel, setConfirmingCancel] = useState(false)
  const startsAt = new Date(event.startsAt)
  const endsAt = new Date(event.endsAt)

  const refresh = () => queryClient.invalidateQueries({ queryKey: calendarEventKeys.all })
  const cancel = useMutation({
    mutationFn: () => calendarEventApi.cancel(event.id),
    onSuccess: () => {
      void refresh()
      onClose()
    },
  })
  const respond = useMutation({
    mutationFn: (accept: boolean) => calendarEventApi.respond(event.id, accept),
    onSuccess: () => {
      void refresh()
      onClose()
    },
  })
  const error = cancel.error ?? respond.error
  const busy = cancel.isPending || respond.isPending

  return (
    <Modal title={event.title} onClose={onClose}>
      <dl className="meeting-details">
        <div>
          <dt>Когда</dt>
          <dd className="meeting-details__when">
            {dayFormat.format(startsAt)}, {timeFormat.format(startsAt)} –{' '}
            {timeFormat.format(endsAt)}
          </dd>
        </div>
        <div>
          <dt>{role === 'employer' ? 'Кандидат' : 'Компания'}</dt>
          <dd>
            {role === 'employer' ? (
              <Link to={paths.matchingProfile('candidate', event.candidate.id)}>
                {event.candidate.name}
              </Link>
            ) : (
              <Link to={paths.company(event.company.id)}>{event.company.name}</Link>
            )}
          </dd>
        </div>
        {event.vacancy && (
          <div>
            <dt>Вакансия</dt>
            <dd>{event.vacancy.name}</dd>
          </div>
        )}
        {event.location && (
          <div>
            <dt>Где</dt>
            <dd>
              {isHttpUrl(event.location) ? (
                <a href={event.location} target="_blank" rel="noreferrer">
                  {event.location}
                </a>
              ) : (
                event.location
              )}
            </dd>
          </div>
        )}
        {event.note && (
          <div>
            <dt>Комментарий</dt>
            <dd className="meeting-details__note">{event.note}</dd>
          </div>
        )}
        <div>
          <dt>Статус</dt>
          <dd>
            <span className={`meeting-status meeting-status--${event.status}`}>
              {MEETING_STATUS_LABELS[event.status]}
            </span>
          </dd>
        </div>
      </dl>

      {error && (
        <p className="meeting-form__status meeting-form__status--error" role="alert">
          {getErrorMessage(error)}
        </p>
      )}

      {role === 'candidate' ? (
        <div className="meeting-details__actions">
          <Button
            disabled={busy || event.status === 'confirmed'}
            onClick={() => respond.mutate(true)}
          >
            {event.status === 'confirmed' ? 'Вы подтвердили' : 'Подтвердить'}
          </Button>
          <Button
            variant="ghost"
            disabled={busy || event.status === 'declined'}
            onClick={() => respond.mutate(false)}
          >
            {event.status === 'declined' ? 'Вы отклонили' : 'Отклонить'}
          </Button>
        </div>
      ) : (
        <div className="meeting-details__actions">
          <Button disabled={busy} onClick={onEdit}>
            Изменить
          </Button>
          {confirmingCancel ? (
            <Button variant="ghost" disabled={busy} onClick={() => cancel.mutate()}>
              {cancel.isPending ? 'Отменяем…' : 'Точно отменить?'}
            </Button>
          ) : (
            <Button variant="ghost" onClick={() => setConfirmingCancel(true)}>
              Отменить встречу
            </Button>
          )}
        </div>
      )}
    </Modal>
  )
}
