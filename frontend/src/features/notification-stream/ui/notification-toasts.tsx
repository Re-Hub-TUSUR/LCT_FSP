import { useCallback, useState } from 'react'
import { Link } from 'react-router'
import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { formatDateTime, plural } from '@/shared/lib'
import { useNotificationStream } from '../model/use-notification-stream'
import './notification-toasts.css'

/** `to`: where the toast leads when there is something to answer. */
type Toast = { id: number; text: string; to?: string }

const SHOWN_MS = 5200
// A toast that asks for an answer stays long enough to be read and clicked.
const ACTION_MS = 9000

export function NotificationToasts() {
  const { user } = useSession()
  const [toasts, setToasts] = useState<Toast[]>([])

  const dismiss = useCallback(
    (id: number) => setToasts((prev) => prev.filter((item) => item.id !== id)),
    [],
  )

  const push = useCallback(
    (text: string, to?: string) => {
      const id = Date.now() + Math.random()
      setToasts((prev) => [...prev, { id, text, to }])
      window.setTimeout(() => dismiss(id), to ? ACTION_MS : SHOWN_MS)
    },
    [dismiss],
  )

  useNotificationStream({
    onCompanyLiked: (event) => {
      if (user?.role !== 'candidate') return
      push(
        event.vacancyTitle
          ? `${event.companyName} отобрала вас на вакансию «${event.vacancyTitle}». Ответить →`
          : `${event.companyName} вас отобрала. Ответить →`,
        ROUTES.profileInvitations,
      )
    },
    onInvitation: (event) => {
      if (user?.role !== 'candidate') return
      push(
        `Приглашение${event.companyName ? ` от ${event.companyName}` : ''}. Открыть →`,
        ROUTES.profileInvitations,
      )
    },
    onMeetingPending: (event) => {
      if (user?.role !== 'candidate') return
      push(
        `${event.companyName} назначила встречу «${event.title}» на ${formatDateTime(event.startsAt)}. Подтвердить →`,
        ROUTES.calendar,
      )
    },
    onSavedSearchNew: (event) => {
      const what =
        event.kind === 'candidates'
          ? plural(event.count, ['новый кандидат', 'новых кандидата', 'новых кандидатов'])
          : plural(event.count, ['новая вакансия', 'новые вакансии', 'новых вакансий'])
      push(`Сохранённый поиск «${event.title}»: ${event.count} ${what}`)
    },
    onCompanyVerification: (event) => {
      if (user?.role !== 'employer') return
      push(
        event.status === 'approved'
          ? 'IT-аккредитация подтверждена'
          : `Выписка отклонена${event.reason ? `: ${event.reason}` : ''}`,
      )
    },
  })

  if (!toasts.length) return null

  return (
    <div className="notify-stack" aria-live="polite">
      {toasts.map((toast) =>
        toast.to ? (
          <Link
            key={toast.id}
            className="notify-stack__item notify-stack__item--link"
            to={toast.to}
            onClick={() => dismiss(toast.id)}
          >
            {toast.text}
          </Link>
        ) : (
          <p key={toast.id} className="notify-stack__item">
            {toast.text}
          </p>
        ),
      )}
    </div>
  )
}
