import { useQuery } from '@tanstack/react-query'
import { Link, useParams } from 'react-router'
import { CandidateCard, candidateQueries } from '@/entities/candidate'
import { CompanyCard, companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { InviteCandidateForm } from '@/features/invite-candidate'
import { ROUTES } from '@/shared/config'
import { EmptyState, Page, QueryState, Section } from '@/shared/ui'

function CandidateProfile({ id }: { id: string }) {
  const { user } = useSession()
  const candidate = useQuery(candidateQueries.detail(id))

  return (
    <QueryState query={candidate}>
      {(data) => (
        <>
          <CandidateCard candidate={data} />
          {user?.role === 'employer' && (
            <>
              <Section title="Встреча">
                <Link
                  className="feed__link"
                  to={`${ROUTES.calendar}?candidateId=${encodeURIComponent(data.id)}`}
                >
                  Назначить встречу в календаре →
                </Link>
              </Section>
              <Section title="Пригласить кандидата">
                <InviteCandidateForm candidateId={data.id} />
              </Section>
            </>
          )}
        </>
      )}
    </QueryState>
  )
}

function CompanyProfile({ id }: { id: string }) {
  const company = useQuery(companyQueries.detail(id))
  return <QueryState query={company}>{(data) => <CompanyCard company={data} />}</QueryState>
}

/** Opened card from the matching deck: candidate (for employers) or company (for candidates). */
export function MatchingProfilePage() {
  const { kind, id = '' } = useParams()

  return (
    <Page title="Профиль">
      {kind === 'candidate' && <CandidateProfile id={id} />}
      {kind === 'company' && <CompanyProfile id={id} />}
      {kind !== 'candidate' && kind !== 'company' && <EmptyState title="Неизвестный тип профиля" />}
    </Page>
  )
}
