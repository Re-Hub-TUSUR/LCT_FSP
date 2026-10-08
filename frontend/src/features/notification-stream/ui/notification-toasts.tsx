import { useCallback, useState } from 'react'
import { useSession } from '@/entities/session'
import { plural } from '@/shared/lib'
import { useNotificationStream } from '../model/use-notification-stream'
import './notification-toasts.css'

type Toast = { id: number; text: string }

export function NotificationToasts() {
  const { user } = useSession()
  const [toasts, setToasts] = useState<Toast[]>([])

  const push = useCallback((text: string) => {
    const id = Date.now()
    setToasts((prev) => [...prev, { id, text }])
    window.setTimeout(() => {
      setToasts((prev) => prev.filter((item) => item.id !== id))
    }, 5200)
  }, [])

  useNotificationStream({
    onCompanyLiked: (event) => {
      if (user?.role !== 'candidate') return
      push(`${event.companyName} вас оценила!`)
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
      {toasts.map((toast) => (
        <p key={toast.id} className="notify-stack__item">
          {toast.text}
        </p>
      ))}
    </div>
  )
}
