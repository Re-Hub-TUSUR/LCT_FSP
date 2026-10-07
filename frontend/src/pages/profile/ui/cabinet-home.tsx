import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { ButtonLink, Page } from '@/shared/ui'
import { CandidateOverview } from './overview/candidate-overview'
import { EmployerOverview } from './overview/employer-overview'

export function CabinetHomePage() {
  const { user } = useSession()
  if (!user) return null
  if (user.role === 'employer') return <EmployerOverview />
  if (user.role === 'candidate') return <CandidateOverview />
  return (
    <Page className="page--inset" title="Кабинет" lead={user.email}>
      <ButtonLink to={ROUTES.admin}>Открыть админку</ButtonLink>
    </Page>
  )
}
