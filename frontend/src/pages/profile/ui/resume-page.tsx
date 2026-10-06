import { useQuery } from '@tanstack/react-query'
import { candidateQueries } from '@/entities/candidate'
import { useSession } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ErrorState, Loader, Page } from '@/shared/ui'
import { ResumeForm } from '@/features/edit-resume'
import { isNotFound } from '../lib/is-not-found'
import { RoleNote } from './role-note'

export function ResumePage() {
  const { user } = useSession()
  const profile = useQuery({ ...candidateQueries.mine(), enabled: user?.role === 'candidate' })

  if (user?.role !== 'candidate') {
    return <RoleNote title="Резюме" text="Резюме заполняет специалист." />
  }
  if (profile.isPending) {
    return (
      <Page className="page--inset" title="Резюме">
        <Loader />
      </Page>
    )
  }
  if (profile.isError && !isNotFound(profile.error)) {
    return (
      <Page className="page--inset" title="Резюме">
        <ErrorState
          message={getErrorMessage(profile.error)}
          onRetry={() => void profile.refetch()}
        />
      </Page>
    )
  }

  const missing = !profile.data

  return (
    <Page
      className={missing ? 'page--inset page--setup' : 'page--inset'}
      title="Резюме"
      lead={
        missing
          ? 'Пока резюме не сохранено, свайпы и остальные разделы закрыты. Грейд здесь не выбирается — его подтверждает тест.'
          : 'Почта берётся из аккаунта. Грейд здесь не выбирается — его подтверждает тест.'
      }
    >
      <ResumeForm profile={profile.data ?? null} />
    </Page>
  )
}
