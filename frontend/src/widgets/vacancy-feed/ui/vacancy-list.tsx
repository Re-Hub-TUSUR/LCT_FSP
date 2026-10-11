import { useState } from 'react'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { VacancyPanel } from './vacancy-panel'
import { VacancyRow } from './vacancy-row'

type Props = {
  items: VacancyMatchDto[]
  /** The candidate's stack: rows say which skills of a vacancy the profile has. */
  profileStack: readonly string[]
}

/**
 * The candidate's vacancies as rows with the side sheet. The same rows in the feed and in
 * «Мои отклики», so a vacancy looks the same wherever the candidate meets it.
 */
export function VacancyList({ items, profileStack }: Props) {
  const [open, setOpen] = useState<VacancyMatchDto | null>(null)
  // The refreshed list knows a decision made in the row after the sheet opened.
  const current = open ? (items.find((item) => item.vacancy.id === open.vacancy.id) ?? open) : null

  return (
    <>
      <div className="feed-table">
        <ol className="feed__list">
          {items.map((match) => (
            <li key={match.vacancy.id}>
              <VacancyRow
                match={match}
                profileStack={profileStack}
                selected={open?.vacancy.id === match.vacancy.id}
                onOpen={() => setOpen(match)}
                actions={
                  <ReactionButtons
                    target="vacancy"
                    id={match.vacancy.id}
                    initial={match.reaction}
                  />
                }
              />
            </li>
          ))}
        </ol>
      </div>
      {current && (
        <VacancyPanel
          key={current.vacancy.id}
          match={current}
          profileStack={profileStack}
          onClose={() => setOpen(null)}
          actions={
            <ReactionButtons target="vacancy" id={current.vacancy.id} initial={current.reaction} />
          }
        />
      )}
    </>
  )
}
