import { useMutation, useQueryClient } from '@tanstack/react-query'
import { invitationApi, invitationKeys, isInvitationFinal } from '@/entities/invitation'
import type { InvitationDecision, InvitationDto } from '@/entities/invitation'
import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui'

export function RespondButtons({ invitation }: { invitation: InvitationDto }) {
  const queryClient = useQueryClient()
  const respond = useMutation({
    mutationFn: (decision: InvitationDecision) => invitationApi.respond(invitation.id, decision),
    onSettled: () => queryClient.invalidateQueries({ queryKey: invitationKeys.list('incoming') }),
  })

  if (isInvitationFinal(invitation.status)) return null

  return (
    <>
      <Button size="inline" disabled={respond.isPending} onClick={() => respond.mutate('accept')}>
        Принять
      </Button>
      <Button
        size="inline"
        variant="ghost"
        disabled={respond.isPending}
        onClick={() => respond.mutate('decline')}
      >
        Отклонить
      </Button>
      {respond.isError && <span role="alert">{getErrorMessage(respond.error)}</span>}
    </>
  )
}
