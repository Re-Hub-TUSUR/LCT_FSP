import { useQuery } from '@tanstack/react-query'
import { useEffect } from 'react'
import { Link, useLocation, useParams, useSearchParams } from 'react-router'
import { CandidateCard, candidateQueries } from '@/entities/candidate'
import { CompanyCard, companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { INVITE_ANCHOR, InviteCandidateForm } from '@/features/invite-candidate'
import { SendAssignmentForm } from '@/features/send-test-assignment'
import { ROUTES } from '@/shared/config'
import { EmptyState, Page, QueryState, Section } from '@/shared/ui'

function CandidateProfile({ id }: { id: string }) {
  const { user } = useSession()
  const candidate = useQuery(candidateQueries.detail(id))
  const [params] = useSearchParams()
  const { hash } = useLocation()
  // «Пригласить» in the bank leads to the form, which is below the card and loads with it.
  const toInvite = hash === `#${INVITE_ANCHOR}` && candidate.isSuccess && user?.role === 'employer'
  useEffect(() => {
    if (toInvite) document.getElementById(INVITE_ANCHOR)?.scrollIntoView()
  }, [toInvite])

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
              <Section title="Тестовое задание">
                <SendAssignmentForm candidateId={data.id} matched={data.matched === true} />
              </Section>
              <div id={INVITE_ANCHOR} className="page-anchor">
                <Section title="Пригласить кандидата">
                  <InviteCandidateForm
                    candidateId={data.id}
                    vacancyId={params.get('vacancyId') ?? undefined}
                  />
                </Section>
              </div>
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
