import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { candidateQueries } from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { useSession } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ErrorState, Loader, Page } from '@/shared/ui'
import { DownloadResumeButton } from '@/features/download-resume'
import { ResumeForm, ResumePanels } from '@/features/edit-resume'
import { isNotFound } from '../lib/is-not-found'
import { RoleNote } from './role-note'

/** The mode is fixed on the first render: right after creation the form keeps its next steps. */
function ResumeEditor({ profile }: { profile: OwnCandidateDto | null }) {
  const [creating] = useState(profile === null)
  if (creating || !profile) return <ResumeForm profile={profile} />
  return <ResumePanels profile={profile} />
}

export function ResumePage() {
  const { user } = useSession()
  const profile = useQuery({ ...candidateQueries.mine(), enabled: user?.role === 'candidate' })

  if (user?.role !== 'candidate') {
    return <RoleNote title="Резюме" text="Резюме заполняет специалист." />
  }
  if (profile.isPending) {
    return (
      <Page className="page--inset" title="Профиль и резюме">
        <Loader />
      </Page>
    )
  }
  if (profile.isError && !isNotFound(profile.error)) {
    return (
      <Page className="page--inset" title="Профиль и резюме">
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
      title={missing ? 'Резюме' : 'Профиль и резюме'}
      actions={
        profile.data ? (
          <DownloadResumeButton candidateId={profile.data.id} name={profile.data.displayName} />
        ) : undefined
      }
      lead={
        missing
          ? 'Пока резюме не сохранено, свайпы и остальные разделы закрыты. Грейд здесь не выбирается — его подтверждает тест.'
          : 'Так вас видит работодатель. Каждый раздел меняется отдельно. Грейд здесь не выбирается — его подтверждает тест.'
      }
    >
      <ResumeEditor profile={profile.data ?? null} />
    </Page>
  )
}
