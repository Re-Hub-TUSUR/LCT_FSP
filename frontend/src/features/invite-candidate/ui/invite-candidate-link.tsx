import { paths } from '@/shared/config'
import { ButtonLink } from '@/shared/ui'

/** The profile page scrolls to the section with this id when the link brings the employer. */
export const INVITE_ANCHOR = 'invite'

type Props = {
  candidateId: string
  /** The vacancy the bank is open for: the invitation is sent for it. */
  vacancyId?: string
}

/** The way from a card of the bank to the invitation: the profile page holds the form. */
export function InviteCandidateLink({ candidateId, vacancyId }: Props) {
  const search = vacancyId ? `?vacancyId=${encodeURIComponent(vacancyId)}` : ''
  return (
    <ButtonLink
      variant="ghost"
      to={`${paths.matchingProfile('candidate', candidateId)}${search}#${INVITE_ANCHOR}`}
    >
      Пригласить
    </ButtonLink>
  )
}
