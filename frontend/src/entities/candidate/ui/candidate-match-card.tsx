import type { ReactNode } from 'react'
import { AssessmentStatusBadge } from '@/entities/assessment/@x/candidate'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy/@x/candidate'
import { useOverflows } from '@/shared/lib'
import { MatchMeter } from '@/shared/ui'
import type { CandidateMatchDto } from '../api/candidate-api'
import { FSP_TITLE_LABELS, bestFspResult, bestFspTitle, fspAchievementLine } from '../model/fsp'
import { CandidateResumes } from './candidate-resumes'
// The slice barrel re-exports this hook, but importing it from there cycles back into this file.
// noinspection JSImportCanBeShortened
import { useCandidatePhoto } from './use-candidate-photo'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
}

/** One line: the best confirmed result and the highest sport title. */
function fspSummary(match: CandidateMatchDto['candidate']): string {
  const best = bestFspResult(match.fspAchievements)
  const title = bestFspTitle(match.fspTitles)
  if (!best && !title) return 'Нет подтверждённой истории участия в ФСП'
  const parts = [
    best ? fspAchievementLine(best) : null,
    title ? FSP_TITLE_LABELS[title.kind] : null,
  ]
  return `ФСП: ${parts.filter(Boolean).join(' · ')}`
}

type Props = {
  match: CandidateMatchDto
  actions?: ReactNode
  /** One film frame. The details button appears only when the profile does not fit. */
  frame?: boolean
  /** Opens the side sheet. Used by the film frame. */
  onStudy?: () => void
}

/** Recruiter's feed card. Contacts are never shown here: only after an accepted invitation. */
export function CandidateMatchCard({ match, actions, frame = false, onStudy }: Props) {
  const { candidate, matchScore, profileStrength, reasons, matched } = match
  const [bodyRef, overflows] = useOverflows(
    frame ? `${candidate.id}:${candidate.about?.length ?? 0}:${reasons.length}` : '',
  )
  const bodyClass = frame
    ? `match-card__frame-body${overflows ? ' is-clipped' : ''}`
    : 'match-card__contents'

  return (
    <article
      className={frame ? 'match-card match-card--frame' : 'match-card'}
      aria-label={candidate.displayName}
    >
      <div ref={frame ? bodyRef : undefined} className={bodyClass}>
        <header className="match-card__head">
          <div className="match-card__person">
            <CandidateAvatar
              candidateId={candidate.id}
              hasPhoto={candidate.hasPhoto === true}
              name={candidate.displayName}
            />
            <div className="match-card__titles">
              <h3 className="match-card__title">{candidate.displayName}</h3>
              {candidate.headline && <p className="match-card__eyebrow">{candidate.headline}</p>}
              {matched && (
                <p className="match-card__matched">Взаимно: кандидат отметил вашу вакансию</p>
              )}
            </div>
          </div>
          <div className="match-card__meters">
            {matchScore !== null && <MatchMeter value={matchScore} label="Под вакансию" />}
            <MatchMeter value={profileStrength} label="Сила профиля" />
          </div>
        </header>

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

        <ul className="match-card__stack" aria-label="Стек">
          {candidate.stack.map((item) => (
            <li key={item}>{item}</li>
          ))}
        </ul>

        <p className="match-card__eyebrow">{fspSummary(candidate)}</p>

        {reasons.length > 0 && (
          <section className="match-card__why" aria-label="Почему кандидат в выдаче">
            <p className="match-card__why-title">Почему в выдаче</p>
            <ul>
              {reasons.map((reason) => (
                <li key={reason}>{reason}</li>
              ))}
            </ul>
          </section>
        )}

        {candidate.about && (
          <div className="match-card__text">
            <p>{candidate.about}</p>
          </div>
        )}

        {actions && <footer className="match-card__actions">{actions}</footer>}
      </div>
      {frame && overflows && onStudy && (
        <button type="button" className="match-card__more match-card__study" onClick={onStudy}>
          Изучить подробнее
        </button>
      )}
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
