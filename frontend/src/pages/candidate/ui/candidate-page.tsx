import { useQuery } from '@tanstack/react-query'
import { useParams } from 'react-router'
import { CandidateCard, candidateQueries } from '@/entities/candidate'
import { DownloadResumeButton } from '@/features/download-resume'
import { Page, QueryState } from '@/shared/ui'

/** Public candidate page. Contacts are returned by the API only when the viewer may see them. */
export function CandidatePage() {
  const { candidateId = '' } = useParams()
  const candidate = useQuery(candidateQueries.detail(candidateId))

  return (
    <Page
      title={candidate.data?.displayName ?? 'Специалист'}
      actions={
        candidate.data ? (
          <DownloadResumeButton candidateId={candidate.data.id} name={candidate.data.displayName} />
        ) : undefined
      }
    >
      <QueryState query={candidate}>{(data) => <CandidateCard candidate={data} />}</QueryState>
    </Page>
  )
}
