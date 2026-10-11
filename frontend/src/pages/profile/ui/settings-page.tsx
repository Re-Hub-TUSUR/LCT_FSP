import { useQuery } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { CandidateCard, candidateQueries } from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { signOut, useSession } from '@/entities/session'
import { ROLE_LABELS } from '@/entities/user'
import type { UserDto } from '@/entities/user'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDate } from '@/shared/lib'
import { Button, ButtonLink, DataRows, ErrorState, Loader, Page, Panel } from '@/shared/ui'
import { OwnerForm } from '@/features/edit-account'
import { JobStatusForm } from '@/features/edit-candidate-settings'
import { FspLinkPanel } from '@/features/link-fsp-id'
import { LockIcon } from './cabinet-icons'

function AccountPanel({ user }: { user: UserDto }) {
  return (
    <Panel
      title="Аккаунт"
      action={
        <Button variant="danger" size="inline" onClick={() => void signOut()}>
          Выйти
        </Button>
      }
    >
      <DataRows
        rows={[
          {
            key: 'email',
            label: 'Email для входа',
            value: user.email,
            note: user.isEmailVerified ? 'Подтверждён' : 'Не подтверждён',
          },
          { key: 'role', label: 'Роль', value: ROLE_LABELS[user.role] },
          { key: 'since', label: 'На платформе с', value: formatDate(user.createdAt) },
        ]}
      />
    </Panel>
  )
}

function CandidateSettings({ user, profile }: { user: UserDto; profile: OwnCandidateDto }) {
  const [params] = useSearchParams()
  return (
    <div className="cabinet-grid">
      <div className="cabinet-col">
        <Panel title="Видимость профиля">
          <JobStatusForm profile={profile} />
          <p className="cabinet-note">
            <LockIcon />
            <span>
              Email и телефон всегда скрыты. Работодатель увидит их, только когда вы примете
              приглашение или откликнетесь на вакансию.
            </span>
          </p>
        </Panel>

        <Panel title="ФСП ID">
          <FspLinkPanel profile={profile} justLinked={params.get('fsp') === 'linked'} />
        </Panel>

        <Panel title="Согласия">
          <DataRows
            rows={[
              {
                key: 'pd',
                label: 'Обработка персональных данных',
                value: `Дано ${formatDate(user.createdAt)}`,
                note: 'По 152-ФЗ, при регистрации.',
              },
              {
                key: 'display',
                label: 'Показ профиля работодателям',
                value: profile.profileDisplayConsent ? 'Дано' : 'Не дано',
                note: 'Профиль виден без контактов. Чтобы скрыть его из банка, выберите статус «Не ищу».',
              },
            ]}
          />
          <p className="form-hint">
            Отзыв согласий и удаление аккаунта пока делаются через поддержку — в кабинете этого ещё
            нет.
          </p>
        </Panel>

        <AccountPanel user={user} />
      </div>

      <div className="cabinet-col">
        <Panel title="Так вас видит работодатель">
          <CandidateCard candidate={{ ...profile, contacts: null }} />
        </Panel>
      </div>
    </div>
  )
}

function CandidateSettingsPage({ user }: { user: UserDto }) {
  const profile = useQuery(candidateQueries.mine())

  let body
  if (profile.isPending) body = <Loader />
  else if (profile.isError) {
    body = (
      <ErrorState message={getErrorMessage(profile.error)} onRetry={() => void profile.refetch()} />
    )
  } else if (!profile.data) {
    body = <ButtonLink to={ROUTES.profileResume}>Создать резюме</ButtonLink>
  } else {
    body = <CandidateSettings user={user} profile={profile.data} />
  }

  return (
    <Page
      className="page--inset"
      title="Настройки"
      lead="Кто видит профиль, связь с ФСП, согласия и вход."
    >
      {body}
    </Page>
  )
}

export function SettingsPage() {
  const { user } = useSession()
  if (!user) return null

  if (user.role === 'candidate') return <CandidateSettingsPage user={user} />

  return (
    <Page
      className="page--inset"
      title="Настройки"
      lead={`${user.email} · ${ROLE_LABELS[user.role]}`}
    >
      <div className="cabinet-grid">
        <div className="cabinet-col">
          {user.role === 'employer' && (
            <Panel title="Контактное лицо">
              <p className="cabinet-muted">
                Человек, который отвечает кандидатам от имени компании.
              </p>
              <OwnerForm submitLabel="Сохранить" />
            </Panel>
          )}
          <AccountPanel user={user} />
        </div>
        {user.role === 'employer' && (
          <div className="cabinet-col">
            <Panel title="Компания">
              <p className="cabinet-muted">Реквизиты, профиль, логотип и IT-аккредитация.</p>
              <div>
                <ButtonLink to={ROUTES.profileCompany} variant="ghost">
                  Профиль компании
                </ButtonLink>
              </div>
            </Panel>
          </div>
        )}
      </div>
    </Page>
  )
}
