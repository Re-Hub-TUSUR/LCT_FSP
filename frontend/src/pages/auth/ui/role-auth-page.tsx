import { useState } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { AuthForm } from '@/features/auth-by-email'
import type { AuthMode } from '@/features/auth-by-email'
import { ROUTES } from '@/shared/config'
import { isSafeInternalPath } from '@/shared/lib'
import { Page } from '@/shared/ui'

const TITLES = {
  candidate: {
    'sign-in': 'Вход для специалиста',
    'sign-up': 'Регистрация специалиста',
    lead: 'Профиль, тестирование и приглашения',
  },
  employer: {
    'sign-in': 'Вход для работодателя',
    'sign-up': 'Регистрация работодателя',
    lead: 'Поиск кандидатов и приглашения',
  },
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
  const [mode, setMode] = useState<AuthMode>(
    params.get('mode') === 'register' ? 'sign-up' : 'sign-in',
  )

  return (
    <Page className="page--auth" title={TITLES[role][mode]} lead={TITLES[role].lead}>
      <AuthForm
        role={role}
        initialEmail={params.get('email') ?? ''}
        initialMode={mode}
        onModeChange={setMode}
        onSuccess={(entry) => {
          const setup = role === 'candidate' ? ROUTES.profileResume : ROUTES.profileCompany
          if (entry === 'verified') {
            navigate(setup, { replace: true })
            return
          }
          navigate(isSafeInternalPath(redirect) ? redirect : ROUTES.feedSwipe, { replace: true })
        }}
      />
    </Page>
  )
}
