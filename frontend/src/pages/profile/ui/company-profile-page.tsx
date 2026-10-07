import { useQuery } from '@tanstack/react-query'
import { useState } from 'react'
import { Link, useNavigate } from 'react-router'
import { CompanyCard, companyQueries } from '@/entities/company'
import { useSession } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ROUTES, paths } from '@/shared/config'
import { ErrorState, Loader, Page, Panel } from '@/shared/ui'
import { CompanyVerification } from '@/features/company-verification'
import { CompanyPanels } from '@/features/edit-company'
import { isNotFound } from '../lib/is-not-found'
import { EmployerSetup } from './employer-setup'
import { RoleNote } from './role-note'

export function CompanyProfilePage() {
  const { user } = useSession()
  const navigate = useNavigate()
  const company = useQuery({ ...companyQueries.mine(), enabled: user?.role === 'employer' })
  // The wizard stays on screen after the company is saved: logo and accreditation come next.
  const [settingUp, setSettingUp] = useState(false)

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

  if (!company.data || settingUp) {
    return (
      <EmployerSetup
        company={company.data ?? null}
        onCompanySaved={() => setSettingUp(true)}
        onDone={() => {
          setSettingUp(false)
          void navigate(ROUTES.profile)
        }}
      />
    )
  }

  return (
    <Page
      className="page--inset"
      title="Компания"
      lead="Эти данные увидит кандидат в приглашении. Контакты специалиста откроются после его согласия."
    >
      <div className="cabinet-grid">
        <div className="cabinet-col">
          <CompanyPanels company={company.data} />
        </div>
        <div className="cabinet-col">
          <Panel title="IT-аккредитация">
            <CompanyVerification bare />
          </Panel>
          <Panel
            title="Так видит кандидат"
            action={
              <Link className="cabinet-link-btn" to={paths.company(company.data.id)}>
                Открыть
              </Link>
            }
          >
            <CompanyCard company={company.data} />
          </Panel>
        </div>
      </div>
    </Page>
  )
}
