import type { ReactNode } from 'react'
import { AssessmentStatusBadge } from '@/entities/assessment/@x/candidate'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy/@x/candidate'
import { MatchMeter } from '@/shared/ui'
import type { CandidateMatchDto, FspAchievementDto } from '../api/candidate-api'
import { FSP_DISCIPLINE_LABELS } from '../model/fsp'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
}

/** Best place first (no place = participation), then the most recent. */
const rank = (item: FspAchievementDto) => (item.place ?? 99) * 10_000 - item.year

function bestResult(items: FspAchievementDto[]) {
  return items.reduce<FspAchievementDto | undefined>(
    (best, item) => (best === undefined || rank(item) < rank(best) ? item : best),
    undefined,
  )
}

type Props = {
  match: CandidateMatchDto
  actions?: ReactNode
}

/** Recruiter's feed card. Contacts are never shown here: only after an accepted invitation. */
export function CandidateMatchCard({ match, actions }: Props) {
  const { candidate, matchScore, profileStrength, reasons } = match
  const best = bestResult(candidate.fspAchievements)

  return (
    <article className="match-card" aria-label={candidate.displayName}>
      <header className="match-card__head">
        <div className="match-card__person">
          <span className="match-card__avatar" aria-hidden="true">
            {initials(candidate.displayName)}
          </span>
          <div className="match-card__titles">
            <h3 className="match-card__title">{candidate.displayName}</h3>
            {candidate.headline && <p className="match-card__eyebrow">{candidate.headline}</p>}
          </div>
        </div>
        <div className="match-card__meters">
          {matchScore !== null && <MatchMeter value={matchScore} label="Под вакансию" />}
          <MatchMeter value={profileStrength} label="Сила профиля" />
        </div>
      </header>

      <ul className="match-card__facts">
        {candidate.category && (
          <li className="match-card__fact match-card__fact--accent">{candidate.category.label}</li>
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

      <ul className="match-card__stack" aria-label="Стек">
        {candidate.stack.map((item) => (
          <li key={item}>{item}</li>
        ))}
      </ul>

      <p className="match-card__eyebrow">
        {best
          ? `ФСП: ${best.place ? `${best.place}-е место` : 'участие'} · ${best.eventName} · ${FSP_DISCIPLINE_LABELS[best.discipline]}, ${best.year}`
          : 'Нет подтверждённой истории участия в ФСП'}
      </p>

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
    </article>
  )
}
