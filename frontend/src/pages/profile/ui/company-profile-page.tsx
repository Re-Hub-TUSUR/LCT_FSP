import { useQuery } from '@tanstack/react-query'
import { companyQueries } from '@/entities/company'
import { signOut, useSession } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { Button, ErrorState, Loader, Page } from '@/shared/ui'
import { CompanyForm } from '@/features/edit-company'
import { isNotFound } from '../lib/is-not-found'
import { RoleNote } from './role-note'

export function CompanyProfilePage() {
  const { user } = useSession()
  const company = useQuery({ ...companyQueries.mine(), enabled: user?.role === 'employer' })

  if (user?.role !== 'employer') {
    return <RoleNote title="Компания" text="Профиль компании заполняет работодатель." />
  }
  if (company.isPending) {
    return (
      <Page className="page--inset" title="Профиль компании">
        <Loader />
      </Page>
    )
  }
  if (company.isError && !isNotFound(company.error)) {
    return (
      <Page className="page--inset" title="Профиль компании">
        <ErrorState
          message={getErrorMessage(company.error)}
          onRetry={() => void company.refetch()}
        />
      </Page>
    )
  }

  const missing = !company.data

  return (
    <Page
      className="page--inset"
      title="Профиль компании"
      lead={
        missing
          ? 'Пока профиль не сохранён, банк кандидатов и остальные разделы закрыты.'
          : 'Эти данные увидит кандидат в приглашении. Контакты специалиста откроются после его согласия.'
      }
      actions={
        missing ? (
          <Button variant="ghost" size="inline" onClick={() => void signOut()}>
            Выйти
          </Button>
        ) : undefined
      }
    >
      <CompanyForm company={company.data ?? null} />
    </Page>
  )
}
