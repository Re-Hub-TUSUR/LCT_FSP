import { useQuery } from '@tanstack/react-query'
import { candidateQueries } from '@/entities/candidate'
import { signOut, useSession } from '@/entities/session'
import { ROLE_LABELS } from '@/entities/user'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDate } from '@/shared/lib'
import { Button, ButtonLink, ErrorState, Loader, Page } from '@/shared/ui'
import { CandidateSettingsForm } from '@/features/edit-candidate-settings'
import { isNotFound } from '../lib/is-not-found'

export function SettingsPage() {
  const { user } = useSession()
  const profile = useQuery({ ...candidateQueries.mine(), enabled: user?.role === 'candidate' })

  if (!user) return null

  return (
    <Page
      className="page--inset"
      title="Настройки"
      lead={`${user.email} · ${ROLE_LABELS[user.role]}`}
      actions={
        <Button variant="ghost" size="inline" onClick={() => void signOut()}>
          Выйти
        </Button>
      }
    >
      <p className="cabinet-copy">
        Согласие на обработку персональных данных принято {formatDate(user.createdAt)}.
      </p>
      {user.role === 'candidate' && profile.isPending && <Loader />}
      {user.role === 'candidate' && profile.isError && !isNotFound(profile.error) && (
        <ErrorState
          message={getErrorMessage(profile.error)}
          onRetry={() => void profile.refetch()}
        />
      )}
      {user.role === 'candidate' && profile.isError && isNotFound(profile.error) && (
        <ButtonLink to={ROUTES.profileResume}>Создать резюме</ButtonLink>
      )}
      {user.role === 'candidate' && profile.data && (
        <CandidateSettingsForm profile={profile.data} />
      )}
      {user.role === 'employer' && (
        <ButtonLink to={ROUTES.profileCompany} variant="ghost">
          Профиль компании
        </ButtonLink>
      )}
    </Page>
  )
}
