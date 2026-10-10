import { paths } from '@/shared/config'
import { ButtonLink } from '@/shared/ui'

/** The way from a card of the bank to the invitation: the profile page holds the form. */
export function InviteCandidateLink({ candidateId }: { candidateId: string }) {
  return (
    <ButtonLink variant="ghost" to={paths.matchingProfile('candidate', candidateId)}>
      Пригласить
    </ButtonLink>
  )
}
