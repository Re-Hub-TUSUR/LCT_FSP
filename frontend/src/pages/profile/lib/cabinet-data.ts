import { useQuery } from '@tanstack/react-query'
import { useOutletContext } from 'react-router'
import { assessmentQueries } from '@/entities/assessment'
import { candidateQueries } from '@/entities/candidate'
import { GRADE_LABELS, categoryQueries } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { companyQueries } from '@/entities/company'
import { invitationQueries } from '@/entities/invitation'
import type { InvitationDto } from '@/entities/invitation'
import { useSession } from '@/entities/session'

export function initialsOf(name: string): string {
  const letters = name
    .split(/\s+/)
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase() ?? '')
  return letters.join('') || '·'
}

export function gradeLabel(grade: string | null): string {
  if (!grade) return ''
  return GRADE_LABELS[grade as Grade] ?? grade
}

/** «Backend-разработка · Middle» from the confirmed category, or null before the test. */
export function useCategoryLabel(): string | null {
  const { user } = useSession()
  const candidate = user?.role === 'candidate'
  const status = useQuery({ ...assessmentQueries.status(), enabled: candidate })
  const dictionary = useQuery({ ...categoryQueries.dictionary(), enabled: candidate })
  const data = status.data
  if (!data || data.status !== 'passed' || !data.specialization) return null
  const spec =
    dictionary.data?.specializations.find((item) => item.code === data.specialization)?.label ??
    data.specialization
  return [spec, gradeLabel(data.grade)].filter(Boolean).join(' · ')
}

/** Waiting for the candidate: new and viewed invitations, newest first. */
export function isWaiting(invitation: InvitationDto) {
  return invitation.status === 'sent' || invitation.status === 'viewed'
}

/**
 * The employer's setup wizard has steps after the company is saved. The flag lives in the layout:
 * the page under it mounts anew when the sections open, and would forget the step it was on.
 */
export type CabinetOutlet = { settingUp: boolean; setSettingUp: (value: boolean) => void }

export function useCabinetOutlet() {
  return useOutletContext<CabinetOutlet>()
}

export function useCabinetData() {
  const { user } = useSession()
  const role = user?.role
  const profile = useQuery({ ...candidateQueries.mine(), enabled: role === 'candidate' })
  const company = useQuery({ ...companyQueries.mine(), enabled: role === 'employer' })
  const invitations = useQuery({
    ...invitationQueries.list(role === 'employer' ? 'outgoing' : 'incoming'),
    enabled: role === 'candidate' || role === 'employer',
  })
  return { user, role, profile, company, invitations }
}
