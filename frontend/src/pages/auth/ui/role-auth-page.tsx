import { useNavigate, useSearchParams } from 'react-router'
import { AuthForm } from '@/features/auth-by-email'
import { ROUTES } from '@/shared/config'
import { isSafeInternalPath } from '@/shared/lib'
import { Page } from '@/shared/ui'

const TITLES = {
  candidate: { title: 'Вход для специалиста', lead: 'Профиль, тестирование и приглашения' },
  employer: { title: 'Вход для работодателя', lead: 'Поиск кандидатов и приглашения' },
} as const

export function EmployerAuthPage() {
  return <RoleAuthPage role="employer" />
}

export function CandidateAuthPage() {
  return <RoleAuthPage role="candidate" />
}

function RoleAuthPage({ role }: { role: 'candidate' | 'employer' }) {
  const navigate = useNavigate()
  const [params] = useSearchParams()
  const redirect = params.get('redirect')

  return (
    <Page className="page--auth" title={TITLES[role].title} lead={TITLES[role].lead}>
      <AuthForm
        role={role}
        initialEmail={params.get('email') ?? ''}
        initialMode={params.get('mode') === 'register' ? 'sign-up' : 'sign-in'}
        onSuccess={() =>
          navigate(isSafeInternalPath(redirect) ? redirect : ROUTES.profile, { replace: true })
        }
      />
    </Page>
  )
}
