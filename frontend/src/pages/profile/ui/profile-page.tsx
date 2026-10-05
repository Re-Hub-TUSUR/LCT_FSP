import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { assessmentQueries } from '@/entities/assessment'
import { CompanyCard, companyQueries } from '@/entities/company'
import { sessionStore, useSession } from '@/entities/session'
import { ROLE_LABELS } from '@/entities/user'
import { ROUTES } from '@/shared/config'
import { formatDate } from '@/shared/lib'
import { Button, Page, QueryState, Section } from '@/shared/ui'
import { InvitationsInbox } from '@/widgets/invitations-inbox'

function CandidateProfile() {
  const status = useQuery(assessmentQueries.status())

  return (
    <>
      <Section title="Категория и грейд">
        <QueryState query={status}>
          {(data) =>
            data.grade ? (
              <p>
                {data.specialization} · {data.grade}
                {data.nextGradeChangeAt &&
                  ` · сменить грейд можно с ${formatDate(data.nextGradeChangeAt)}`}
              </p>
            ) : (
              <p>
                Категория ещё не присвоена. <Link to={ROUTES.testing}>Пройти опрос и тест</Link>
              </p>
            )
          }
        </QueryState>
      </Section>
      <Section title="Приглашения от работодателей">
        <InvitationsInbox direction="incoming" />
      </Section>
      {/* TODO(profile): resume form / PDF import, privacy settings, FSP ID linking. */}
    </>
  )
}

function EmployerProfile() {
  const company = useQuery(companyQueries.mine())

  return (
    <>
      <Section title="Компания">
        <QueryState query={company}>{(data) => <CompanyCard company={data} />}</QueryState>
      </Section>
      <Section title="Отправленные приглашения">
        <InvitationsInbox direction="outgoing" />
      </Section>
      <Link to={ROUTES.feed}>Перейти к подбору кандидатов</Link>
    </>
  )
}

export function ProfilePage() {
  const { user } = useSession()
  if (!user) return null

  return (
    <Page
      title="Личный кабинет"
      lead={`${user.email} · ${ROLE_LABELS[user.role]}`}
      actions={
        <Button variant="ghost" size="inline" onClick={() => sessionStore.clear()}>
          Выйти
        </Button>
      }
    >
      {user.role === 'candidate' && <CandidateProfile />}
      {user.role === 'employer' && <EmployerProfile />}
      {user.role === 'admin' && <Link to={ROUTES.admin}>Открыть админку</Link>}
    </Page>
  )
}
