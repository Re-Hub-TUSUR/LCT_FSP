import type { ReactNode } from 'react'
import { AssessmentStatusBadge } from '@/entities/assessment'
import { CandidateResumes, useCandidatePhoto } from '@/entities/candidate'
import type { CandidateMatchDto } from '@/entities/candidate'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { MatchMeter } from '@/shared/ui'
import './candidate-sheet.css'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
}

type Props = {
  match: CandidateMatchDto
  selected: boolean
  onOpen: () => void
  actions?: ReactNode
}

/** Feed row for an employer. The full profile, including FSP and the bio, opens in the side panel. */
export function CandidateRow({ match, selected, onOpen, actions }: Props) {
  const { candidate, matchScore, profileStrength, matched } = match

  return (
    <article
      className={selected ? 'match-card is-open' : 'match-card'}
      aria-label={candidate.displayName}
    >
      <button
        type="button"
        className="candidate-row__open"
        aria-expanded={selected}
        onClick={onOpen}
      >
        <span className="match-card__head">
          <span className="match-card__person">
            <CandidateAvatar
              candidateId={candidate.id}
              hasPhoto={candidate.hasPhoto === true}
              name={candidate.displayName}
            />
            <span className="match-card__titles">
              <span className="match-card__title">{candidate.displayName}</span>
              {candidate.headline && (
                <span className="match-card__eyebrow">{candidate.headline}</span>
              )}
              {matched && (
                <span className="match-card__matched">Взаимно: кандидат отметил вашу вакансию</span>
              )}
            </span>
          </span>
          <span className="match-card__meters">
            {matchScore !== null && <MatchMeter value={matchScore} label="Под вакансию" />}
            <MatchMeter value={profileStrength} label="Сила профиля" />
          </span>
        </span>

        <ul className="match-card__facts">
          {candidate.category && (
            <li className="match-card__fact match-card__fact--accent">
              {candidate.category.label}
            </li>
          )}
          <li>
            <AssessmentStatusBadge
              status={candidate.assessmentStatus}
              score={candidate.assessmentScore}
            />
          </li>
          {candidate.experienceYears !== null && (
            <li className="match-card__fact">Опыт: {candidate.experienceYears} г.</li>
          )}
          {candidate.city && (
            <li className="match-card__fact">
              {candidate.city}
              {candidate.relocationReady ? ' · переезд' : ''}
            </li>
          )}
          {candidate.workFormats.map((format) => (
            <li key={format} className="match-card__fact">
              {WORK_FORMAT_LABELS[format]}
            </li>
          ))}
          {candidate.salaryExpectation !== null && (
            <li className="match-card__fact">от {rub.format(candidate.salaryExpectation)} ₽</li>
          )}
        </ul>

        <CandidateResumes candidate={candidate} />

        {candidate.stack.length > 0 && (
          <ul className="match-card__stack" aria-label="Стек">
            {candidate.stack.map((item) => (
              <li key={item}>{item}</li>
            ))}
          </ul>
        )}
      </button>
      {actions && <footer className="match-card__actions">{actions}</footer>}
    </article>
  )
}

function CandidateAvatar({
  candidateId,
  hasPhoto,
  name,
}: {
  candidateId: string
  hasPhoto: boolean
  name: string
}) {
  const photo = useCandidatePhoto(candidateId, hasPhoto)
  if (photo.data) return <img className="match-card__photo" src={photo.data} alt="" />
  return (
    <span className="match-card__avatar" aria-hidden="true">
      {initials(name)}
    </span>
  )
}
