import { useQuery } from '@tanstack/react-query'
import { InvitationCard, invitationQueries } from '@/entities/invitation'
import type { InvitationDirection } from '@/entities/invitation'
import { RespondButtons } from '@/features/respond-to-invitation'
import { QueryState } from '@/shared/ui'
import './invitations-inbox.css'

/** Candidate's inbox (with accept/decline) or employer's list of sent invitations. */
export function InvitationsInbox({ direction }: { direction: InvitationDirection }) {
  const query = useQuery(invitationQueries.list(direction))

  return (
    <QueryState
      query={query}
      isEmpty={(page) => page.items.length === 0}
      emptyTitle={direction === 'incoming' ? 'Приглашений пока нет' : 'Вы ещё никого не пригласили'}
    >
      {(page) => (
        <ul className="invitations-inbox">
          {page.items.map((invitation) => (
            <li key={invitation.id}>
              <InvitationCard
                invitation={invitation}
                actions={
                  direction === 'incoming' ? <RespondButtons invitation={invitation} /> : undefined
                }
              />
            </li>
          ))}
        </ul>
      )}
    </QueryState>
  )
}
