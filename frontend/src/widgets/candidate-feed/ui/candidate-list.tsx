import { useState, type ReactNode } from 'react'
import type { CandidateMatchDto } from '@/entities/candidate'
import type { ListView } from '@/entities/vacancy'
import { ReactionButtons } from '@/features/feed-reaction'
import { InviteCandidateLink } from '@/features/invite-candidate'
import { CandidatePanel } from './candidate-panel'
import { CandidateRow } from './candidate-row'

type Props = {
  items: CandidateMatchDto[]
  /** A skipped candidate is dimmed everywhere but in the list of skipped ones. */
  view: ListView
  /** The feed opened for a vacancy: likes and invitations are for it. */
  vacancyId?: string
  /** Something more in a row, after the decisions. */
  rowExtra?: (match: CandidateMatchDto) => ReactNode
}

/**
 * The employer's candidates as table rows with the side sheet. The same rows in the feed and in
 * «Мои отклики», so a candidate looks the same wherever the recruiter meets them.
 */
export function CandidateList({ items, view, vacancyId, rowExtra }: Props) {
  const [open, setOpen] = useState<CandidateMatchDto | null>(null)
  // The refreshed list knows a decision made in the row after the sheet opened.
  const current = open
    ? (items.find((item) => item.candidate.id === open.candidate.id) ?? open)
    : null

  return (
    <>
      <div className="feed-table">
        <div className="feed-table__head candidate-row__grid" aria-hidden="true">
          <span>Кандидат</span>
          <span>Тест</span>
          <span>Под вакансию</span>
          <span>Ожидания</span>
          <span>Решение</span>
        </div>
        <ol className="feed__list">
          {items.map((match) => (
            <li key={match.candidate.id}>
              <CandidateRow
                match={match}
                dimmed={match.reaction === 'skip' && view !== 'skipped'}
                selected={open?.candidate.id === match.candidate.id}
                onOpen={() => setOpen(match)}
                actions={
                  <>
                    <ReactionButtons
                      target="candidate"
                      id={match.candidate.id}
                      initial={match.reaction}
                      vacancyId={vacancyId}
                    />
                    {rowExtra?.(match)}
                  </>
                }
              />
            </li>
          ))}
        </ol>
      </div>
      {current && (
        <CandidatePanel
          key={current.candidate.id}
          match={current}
          onClose={() => setOpen(null)}
          actions={
            <>
              <ReactionButtons
                target="candidate"
                id={current.candidate.id}
                initial={current.reaction}
                vacancyId={vacancyId}
              />
              <InviteCandidateLink candidateId={current.candidate.id} vacancyId={vacancyId} />
            </>
          }
        />
      )}
    </>
  )
}
