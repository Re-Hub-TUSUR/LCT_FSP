import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { assessmentQueries } from '@/entities/assessment'
import { candidateQueries } from '@/entities/candidate'
import { GRADE_LABELS, categoryQueries } from '@/entities/category'
import type { Grade } from '@/entities/category'
import { CompanyCard, companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { CompanyForm } from '@/features/edit-company'
import { ApiError, getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { ButtonLink, EmptyState, ErrorState, Loader, Page } from '@/shared/ui'
import { InvitationsInbox } from '@/widgets/invitations-inbox'
import { isNotFound } from '../lib/is-not-found'

type Step = { id: string; title: string; done: boolean }

function CandidateHome() {
  const profile = useQuery(candidateQueries.mine())
  const assessment = useQuery({
    ...assessmentQueries.status(),
    enabled: profile.isSuccess,
  })
  const dictionary = useQuery({
    ...categoryQueries.dictionary(),
    enabled: profile.isSuccess,
  })

  if (profile.isPending) {
    return (
      <Page className="page--inset" title="Кабинет">
        <Loader />
      </Page>
    )
  }
  if (profile.isError && !isNotFound(profile.error)) {
    return (
      <Page className="page--inset" title="Кабинет">
        <ErrorState
          message={getErrorMessage(profile.error)}
          onRetry={() => void profile.refetch()}
        />
      </Page>
    )
  }
  if (!profile.data) return <Onboarding />

  if (assessment.isPending) {
    return (
      <Page className="page--inset" title="Приглашения">
        <Loader />
      </Page>
    )
  }
  if (
    assessment.isError &&
    !(assessment.error instanceof ApiError && assessment.error.status === 501)
  ) {
    return (
      <Page className="page--inset" title="Приглашения">
        <ErrorState
          message={getErrorMessage(assessment.error)}
          onRetry={() => void assessment.refetch()}
        />
      </Page>
    )
  }

  const steps: Step[] = [
    { id: 'resume', title: 'Резюме', done: true },
    { id: 'test', title: 'Тест', done: assessment.data?.status === 'passed' },
    { id: 'fsp', title: 'Связь с ФСП', done: profile.data.fspLinked },
  ]
  const current = steps.find((step) => !step.done)

  return (
    <Page
      className="page--inset"
      title="Приглашения"
      lead={
        current
          ? 'Сначала завершите текущий шаг — приглашения уже можно смотреть.'
          : 'Новые предложения сверху.'
      }
    >
      {current && (
        <>
          <ol className="steps">
            {steps.map((step, index) => (
              <li
                key={step.id}
                className={`steps__item${step.done ? ' is-done' : ''}${step.id === current.id ? ' is-current' : ''}`}
                aria-current={step.id === current.id ? 'step' : undefined}
              >
                <span className="steps__index" aria-hidden="true">
                  0{index + 1}
                </span>
                <span>
                  <span className="steps__title">{step.title}</span>
                  <span className="steps__state">
                    {step.done ? 'Готово' : step.id === current.id ? 'Сейчас' : 'Дальше'}
                  </span>
                </span>
              </li>
            ))}
          </ol>
          <StepAction id={current.id} />
        </>
      )}
      {assessment.data?.status === 'passed' && (
        <p className="cabinet-copy">
          {labelOf(dictionary.data?.specializations, assessment.data.specialization)}
          {assessment.data.grade
            ? ` · ${GRADE_LABELS[assessment.data.grade as Grade] ?? assessment.data.grade}`
            : ''}
        </p>
      )}
      <InvitationsInbox
        direction="incoming"
        empty={
          <EmptyState title="Приглашений пока нет">
            <Link className="cabinet-link" to={ROUTES.feed}>
              Смотреть вакансии
            </Link>
          </EmptyState>
        }
      />
    </Page>
  )
}

function labelOf(
  items: { code: string; label: string }[] | undefined,
  code: string | null,
): string {
  if (!code) return 'Категория подтверждена'
  return items?.find((item) => item.code === code)?.label ?? code
}

function StepAction({ id }: { id: string }) {
  if (id === 'test') return <ButtonLink to={ROUTES.testing}>Пройти тест</ButtonLink>
  if (id === 'fsp') return <ButtonLink to={ROUTES.profileSettings}>Связать с ФСП</ButtonLink>
  return <ButtonLink to={ROUTES.profileResume}>Создать резюме</ButtonLink>
}

function Onboarding() {
  const steps = [
    { title: 'Резюме', state: 'Сейчас' },
    { title: 'Тест', state: 'Дальше' },
    { title: 'Связь с ФСП', state: 'Дальше' },
  ]
  return (
    <Page
      className="page--inset"
      title="Кабинет"
      lead="Резюме, тест на грейд и связь с ФСП. После этого работодатели видят вас в подборке."
    >
      <ol className="steps">
        {steps.map((step, index) => (
          <li
            key={step.title}
            className={`steps__item${index === 0 ? ' is-current' : ''}`}
            aria-current={index === 0 ? 'step' : undefined}
          >
            <span className="steps__index" aria-hidden="true">
              0{index + 1}
            </span>
            <span>
              <span className="steps__title">{step.title}</span>
              <span className="steps__state">{step.state}</span>
            </span>
          </li>
        ))}
      </ol>
      <ButtonLink to={ROUTES.profileResume}>Создать резюме</ButtonLink>
    </Page>
  )
}

function EmployerHome() {
  const company = useQuery(companyQueries.mine())

  if (company.isPending) {
    return (
      <Page className="page--inset" title="Кабинет">
        <Loader />
      </Page>
    )
  }
  if (company.isError && !isNotFound(company.error)) {
    return (
      <Page className="page--inset" title="Кабинет">
        <ErrorState
          message={getErrorMessage(company.error)}
          onRetry={() => void company.refetch()}
        />
      </Page>
    )
  }
  if (!company.data) {
    return (
      <Page
        className="page--inset"
        title="Профиль компании"
        lead="Название, чем занимаетесь и как с вами связаться. Без этого приглашения недоступны."
      >
        <CompanyForm company={null} />
      </Page>
    )
  }

  return (
    <Page
      className="page--inset"
      title="Кабинет"
      lead={company.data.name}
      actions={<ButtonLink to={ROUTES.feed}>Открыть банк кандидатов</ButtonLink>}
    >
      <CompanyCard
        company={company.data}
        actions={
          <ButtonLink to={ROUTES.profileCompany} variant="ghost">
            Изменить
          </ButtonLink>
        }
      />
      <p className="cabinet-copy">
        Контакты кандидата откроются после того, как он примет приглашение.
      </p>
      <InvitationsInbox direction="outgoing" empty={<EmptyState title="Приглашений пока нет" />} />
    </Page>
  )
}

export function CabinetHomePage() {
  const { user } = useSession()
  if (!user) return null
  if (user.role === 'employer') return <EmployerHome />
  if (user.role === 'candidate') return <CandidateHome />
  return (
    <Page className="page--inset" title="Кабинет" lead={user.email}>
      <ButtonLink to={ROUTES.admin}>Открыть админку</ButtonLink>
    </Page>
  )
}
