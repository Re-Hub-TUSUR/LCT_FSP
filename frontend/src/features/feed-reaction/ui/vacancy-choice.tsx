import { useState } from 'react'
import type { ReactNode } from 'react'
import { useQuery } from '@tanstack/react-query'
import { useSession } from '@/entities/session'
import { vacancyQueries } from '@/entities/vacancy'
import type { VacancyDto } from '@/entities/vacancy'
import { formatRubRange } from '@/shared/lib'
import { Modal } from '@/shared/ui'
import './vacancy-choice.css'

const LAST_KEY = 'kadry.like-vacancy'

function lastChosen(): string | null {
  try {
    return window.localStorage.getItem(LAST_KEY)
  } catch {
    return null
  }
}

function remember(vacancyId: string) {
  try {
    window.localStorage.setItem(LAST_KEY, vacancyId)
  } catch {
    // Private mode: the last choice is simply not offered first next time.
  }
}

type Pending = { onChosen: (vacancyId: string) => void; onCancel?: () => void }

/**
 * Which of the company's vacancies a like is sent for. The candidate sees that vacancy in the
 * like, so the recruiter names it: asked only when the company has several published ones.
 */
export function useLikeVacancy(): {
  /** Calls `onChosen` with the vacancy (none when the company has no published one). */
  ask: (onChosen: (vacancyId: string | undefined) => void, onCancel?: () => void) => void
  dialog: ReactNode
} {
  const { user } = useSession()
  const mine = useQuery({ ...vacancyQueries.mine(), enabled: user?.role === 'employer' })
  const [pending, setPending] = useState<Pending | null>(null)
  const published = (mine.data?.items ?? []).filter((vacancy) => vacancy.publishedAt)

  const ask = (onChosen: (vacancyId: string | undefined) => void, onCancel?: () => void) => {
    if (published.length <= 1) return onChosen(published[0]?.id)
    setPending({ onChosen, onCancel })
  }

  const dialog = pending ? (
    <VacancyChoiceDialog
      vacancies={published}
      onPick={(vacancyId) => {
        remember(vacancyId)
        setPending(null)
        pending.onChosen(vacancyId)
      }}
      onClose={() => {
        setPending(null)
        pending.onCancel?.()
      }}
    />
  ) : null

  return { ask, dialog }
}

type Props = {
  vacancies: VacancyDto[]
  onPick: (vacancyId: string) => void
  onClose: () => void
}

function VacancyChoiceDialog({ vacancies, onPick, onClose }: Props) {
  const last = lastChosen()
  // The vacancy chosen last time goes first: a recruiter usually hires for one at a time.
  const ordered = [
    ...vacancies.filter((vacancy) => vacancy.id === last),
    ...vacancies.filter((vacancy) => vacancy.id !== last),
  ]

  return (
    <Modal title="На какую вакансию отбираете?" onClose={onClose}>
      <p className="vacancy-choice__lead">
        Кандидат увидит эту вакансию в уведомлении и в «Приглашениях».
      </p>
      <ul className="vacancy-choice__list">
        {ordered.map((vacancy) => (
          <li key={vacancy.id}>
            <button
              type="button"
              className="vacancy-choice__option"
              onClick={() => onPick(vacancy.id)}
            >
              <span>{vacancy.title}</span>
              <span className="vacancy-choice__hint">
                {vacancy.category.label} · {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
                {vacancy.id === last ? ' · выбирали в прошлый раз' : ''}
              </span>
            </button>
          </li>
        ))}
      </ul>
    </Modal>
  )
}
