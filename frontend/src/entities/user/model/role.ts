export const USER_ROLES = ['candidate', 'employer', 'admin'] as const

export type UserRole = (typeof USER_ROLES)[number]

export const ROLE_LABELS: Record<UserRole, string> = {
  candidate: 'Специалист',
  employer: 'Работодатель',
  admin: 'Администратор',
}
