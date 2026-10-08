import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import { INVITATION_STATUS_LABELS } from '@/entities/invitation'
import type { InvitationDirection, InvitationDto } from '@/entities/invitation'
import { ROUTES } from '@/shared/config'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { Avatar } from '@/shared/ui'

const LIMIT = 5

/** The employer's list stores only the candidate id: the name and category come from the profile. */
function useCounterpart(item: InvitationDto, direction: InvitationDirection) {
  const candidate = useQuery({
    ...candidateQueries.detail(item.candidateId),
    enabled: direction === 'outgoing',
  })
  if (direction === 'incoming') return { name: item.company.name, note: null }
  return {
    name: candidate.data?.displayName ?? 'Кандидат',
    note: candidate.data?.category?.label ?? null,
  }
}

function WaitingCard({ item, direction }: { item: InvitationDto; direction: InvitationDirection }) {
  const { name, note } = useCounterpart(item, direction)
  // «Отправлено» still needs a look; «Просмотрено» is only waiting for the decision.
  const fresh = item.status === 'sent'

  return (
    <Link
      className={fresh ? 'wait-card is-fresh' : 'wait-card'}
      to={`${ROUTES.profileInvitations}?id=${item.id}`}
    >
      <Avatar name={name} size="lg" tone="dark" />
      <span className="wait-card__main">
        <span className="wait-card__title">{name}</span>
        <span className="wait-card__sub">
          {[note, formatDateTime(item.createdAt)].filter(Boolean).join(' · ')}
        </span>
      </span>
      <span className="wait-card__side">
        <span className="wait-card__salary">
          {formatRubRange(item.salary.from, item.salary.to)}
        </span>
        <span className="wait-card__status">{INVITATION_STATUS_LABELS[item.status]}</span>
      </span>
    </Link>
  )
}

export function WaitingList({
  items,
  direction,
  emptyText,
}: {
  items: InvitationDto[]
  direction: InvitationDirection
  emptyText: string
}) {
  if (items.length === 0) return <p className="cabinet-muted cabinet-muted--plate">{emptyText}</p>
  return (
    <div className="wait-list">
      {items.slice(0, LIMIT).map((item) => (
        <WaitingCard key={item.id} item={item} direction={direction} />
      ))}
    </div>
  )
}
