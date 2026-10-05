/** Lifecycle of an employer → candidate invitation (ТЗ 2.2, item 3). */
export const INVITATION_STATUSES = ['sent', 'viewed', 'accepted', 'declined'] as const

export type InvitationStatus = (typeof INVITATION_STATUSES)[number]

export const INVITATION_STATUS_LABELS: Record<InvitationStatus, string> = {
  sent: 'Отправлено',
  viewed: 'Просмотрено',
  accepted: 'Принято',
  declined: 'Отклонено',
}

export function isInvitationFinal(status: InvitationStatus): boolean {
  return status === 'accepted' || status === 'declined'
}
