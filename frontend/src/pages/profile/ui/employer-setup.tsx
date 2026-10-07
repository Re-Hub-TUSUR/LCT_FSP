import { useState } from 'react'
import type { CompanyDto } from '@/entities/company'
import { signOut, useSession } from '@/entities/session'
import { OwnerForm } from '@/features/edit-account'
import { CompanyVerification } from '@/features/company-verification'
import { CompanyForm, EMPTY_LEGAL, LegalForm, LogoField } from '@/features/edit-company'
import type { LegalValues } from '@/features/edit-company'
import { Button, Page } from '@/shared/ui'

type Step = 'owner' | 'legal' | 'profile' | 'extras'

const STEPS: { title: string; covers: Step[] }[] = [
  { title: 'О вас', covers: ['owner'] },
  { title: 'Компания', covers: ['legal'] },
  { title: 'Профиль', covers: ['profile', 'extras'] },
]

const LEADS: Record<Step, string> = {
  owner: 'Кто отвечает кандидатам. Имя увидят в приглашениях, телефон — только администратор.',
  legal: 'ИНН и реквизиты. По ним администратор сверит выписку Минцифры.',
  profile: 'Так компанию увидят кандидаты в ленте и в приглашениях.',
  extras: 'Логотип и IT-аккредитация. Можно добавить и позже на странице компании.',
}

type Props = {
  company: CompanyDto | null
  /** Called before the saved company reaches the cache, so the page keeps the wizard. */
  onCompanySaved: () => void
  onDone: () => void
}

/** Employer setup after the email is confirmed: three steps from the spec. */
export function EmployerSetup({ company, onCompanySaved, onDone }: Props) {
  const { user } = useSession()
  const [step, setStep] = useState<Step>(() =>
    user?.firstName && user.lastName ? 'legal' : 'owner',
  )
  const [legal, setLegal] = useState<LegalValues>(EMPTY_LEGAL)
  const current = STEPS.findIndex((item) => item.covers.includes(step))

  return (
    <Page
      className="page--inset"
      title="Настройка компании"
      lead={
        step === 'extras'
          ? LEADS.extras
          : `${LEADS[step]} Пока компания не сохранена, остальные разделы закрыты.`
      }
      actions={
        <Button variant="ghost" size="inline" onClick={() => void signOut()}>
          Выйти
        </Button>
      }
    >
      <ol className="steps">
        {STEPS.map((item, index) => (
          <li
            key={item.title}
            className={`steps__item${index < current ? ' is-done' : ''}${index === current ? ' is-current' : ''}`}
            aria-current={index === current ? 'step' : undefined}
          >
            <span className="steps__index" aria-hidden="true">
              0{index + 1}
            </span>
            <span>
              <span className="steps__title">{item.title}</span>
              <span className="steps__state">
                {index < current ? 'Готово' : index === current ? 'Сейчас' : 'Дальше'}
              </span>
            </span>
          </li>
        ))}
      </ol>

      {step === 'owner' && <OwnerForm onSaved={() => setStep('legal')} />}
      {step === 'legal' && (
        <LegalForm
          initial={legal}
          onBack={() => setStep('owner')}
          onNext={(values) => {
            setLegal(values)
            setStep('profile')
          }}
        />
      )}
      {step === 'profile' && (
        <CompanyForm
          company={company}
          legal={legal}
          onBack={() => setStep('legal')}
          onSaved={() => {
            onCompanySaved()
            setStep('extras')
          }}
        />
      )}
      {step === 'extras' && company && (
        <>
          <LogoField company={company} />
          <CompanyVerification />
          <div className="form-actions">
            <Button size="inline" onClick={onDone}>
              Перейти в кабинет
            </Button>
          </div>
        </>
      )}
    </Page>
  )
}
