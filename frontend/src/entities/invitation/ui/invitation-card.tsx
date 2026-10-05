import type { ReactNode } from 'react'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { Tag } from '@/shared/ui'
import type { InvitationDto } from '../api/invitation-api'
import { INVITATION_STATUS_LABELS } from '../model/status'
import './invitation-card.css'

export function InvitationCard({
  invitation,
  actions,
}: {
  invitation: InvitationDto
  actions?: ReactNode
}) {
  const { company, salary, message, contactMethod, status, createdAt } = invitation

  return (
    <article className="invitation-card" aria-label={`Приглашение от ${company.name}`}>
      <header className="invitation-card__header">
        <h3 className="invitation-card__company">{company.name}</h3>
        <Tag>{INVITATION_STATUS_LABELS[status]}</Tag>
      </header>
      <p className="invitation-card__salary">{formatRubRange(salary.from, salary.to)}</p>
      <p className="invitation-card__message">{message}</p>
      <p className="invitation-card__meta">
        Связь: {contactMethod} · {formatDateTime(createdAt)}
      </p>
      {actions && <footer className="invitation-card__actions">{actions}</footer>}
    </article>
  )
}
