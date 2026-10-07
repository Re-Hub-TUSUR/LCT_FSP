import { Link } from 'react-router'
import type { InvitationDirection, InvitationDto } from '@/entities/invitation'
import { ROUTES } from '@/shared/config'
import { formatDateTime, formatRubRange } from '@/shared/lib'
import { CandidateName, InvitationStatusTag } from '@/widgets/invitations-inbox'

const LIMIT = 5

export function WaitingList({
  items,
  direction,
  emptyText,
}: {
  items: InvitationDto[]
  direction: InvitationDirection
  emptyText: string
}) {
  if (items.length === 0) return <p className="cabinet-muted">{emptyText}</p>
  return (
    <div>
      {items.slice(0, LIMIT).map((item) => (
        <div key={item.id} className="wait-row">
          <div>
            <div className="wait-row__top">
              <InvitationStatusTag status={item.status} direction={direction} />
              <span className="cabinet-time">{formatDateTime(item.createdAt)}</span>
            </div>
            <p className="wait-row__title">
              {direction === 'incoming' ? (
                item.company.name
              ) : (
                <CandidateName id={item.candidateId} />
              )}
            </p>
          </div>
          <p className="cabinet-salary">{formatRubRange(item.salary.from, item.salary.to)}</p>
          <Link className="cabinet-link-btn" to={`${ROUTES.profileInvitations}?id=${item.id}`}>
            Открыть
          </Link>
        </div>
      ))}
    </div>
  )
}
