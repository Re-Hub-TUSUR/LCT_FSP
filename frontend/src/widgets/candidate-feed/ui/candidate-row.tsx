import type { ReactNode } from 'react'
import { AssessmentStatusBadge } from '@/entities/assessment'
import { useCandidatePhoto } from '@/entities/candidate'
import type { CandidateMatchDto } from '@/entities/candidate'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { Avatar, MatchMeter } from '@/shared/ui'
import './candidate-sheet.css'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

type Props = {
  match: CandidateMatchDto
  selected: boolean
  /** A skipped candidate still shown in the main list. */
  dimmed?: boolean
  onOpen: () => void
  actions?: ReactNode
}

/** Table row of the employer's feed. The full profile, FSP and the bio open in the side sheet. */
export function CandidateRow({ match, selected, dimmed = false, onOpen, actions }: Props) {
  const { candidate, matchScore, profileStrength, matched } = match
  const photo = useCandidatePhoto(candidate.id, candidate.hasPhoto === true)
  const place = candidate.city
    ? `${candidate.city}${candidate.relocationReady ? ' · переезд' : ''}`
    : null
  const classes = [
    'candidate-row',
    'candidate-row__grid',
    selected && 'is-open',
    dimmed && 'is-dim',
  ]
    .filter(Boolean)
    .join(' ')

  return (
    // The name is the keyboard way in; a click anywhere on the row is a shortcut for the mouse.
    // oxlint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
    <article className={classes} aria-label={candidate.displayName} onClick={onOpen}>
      <div className="candidate-row__person">
        <Avatar name={candidate.displayName} src={photo.data} />
        <div className="candidate-row__titles">
          <button
            type="button"
            className="candidate-row__name"
            aria-expanded={selected}
            onClick={(event) => {
              event.stopPropagation()
              onOpen()
            }}
          >
            {candidate.displayName}
          </button>
          {(candidate.headline || place) && (
            <span className="candidate-row__sub">
              {[candidate.headline, place].filter(Boolean).join(' · ')}
            </span>
          )}
          {matched && <span className="candidate-row__matched">Взаимно</span>}
        </div>
      </div>

      <div className="candidate-row__tags">
        {candidate.category && <span className="tag">{candidate.category.label}</span>}
        <AssessmentStatusBadge
          status={candidate.assessmentStatus}
          score={candidate.assessmentScore}
        />
      </div>

      <div className="candidate-row__meter">
        <MatchMeter compact value={matchScore} label="Под вакансию" />
      </div>
      <div className="candidate-row__meter">
        <MatchMeter compact value={profileStrength} label="Сила профиля" />
      </div>

      <div className="candidate-row__pay">
        <span className="candidate-row__salary">
          {candidate.salaryExpectation !== null
            ? `от ${rub.format(candidate.salaryExpectation)} ₽`
            : 'Не указано'}
        </span>
        {candidate.workFormats.length > 0 && (
          <span className="candidate-row__sub">
            {candidate.workFormats.map((format) => WORK_FORMAT_LABELS[format]).join(' · ')}
          </span>
        )}
      </div>

      {actions && (
        // Buttons inside the row decide on their own; they must not open the sheet.
        // oxlint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-static-element-interactions
        <div className="candidate-row__actions" onClick={(event) => event.stopPropagation()}>
          {actions}
        </div>
      )}
    </article>
  )
}
