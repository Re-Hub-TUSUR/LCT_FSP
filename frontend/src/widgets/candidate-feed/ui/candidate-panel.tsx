import { useId, type ReactNode } from 'react'
import { AssessmentStatusBadge } from '@/entities/assessment'
import { CandidateResumes, FSP_DISCIPLINE_LABELS, useCandidatePhoto } from '@/entities/candidate'
import type { CandidateMatchDto, FspAchievementDto } from '@/entities/candidate'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { Avatar, ChipList, MatchMeter, Sheet, SheetSection } from '@/shared/ui'
import './candidate-sheet.css'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

const FSP_LEVELS = {
  regional: 'региональный',
  national: 'всероссийский',
  international: 'международный',
} as const

function achievementLine(item: FspAchievementDto) {
  const place = item.place ? `${item.place}-е место` : 'участие'
  return `${place} · ${item.eventName} · ${FSP_DISCIPLINE_LABELS[item.discipline]}, ${item.year} · ${FSP_LEVELS[item.level]}`
}

/** Comparisons with the chosen vacancy. Test, FSP, stack and city are already on the sheet. */
function vacancyNotes(reasons: string[]) {
  return reasons.filter((reason) =>
    /^(Смежная специализация:|Грейд на ступень|Ожидания )/.test(reason),
  )
}

type Props = {
  match: CandidateMatchDto
  onClose: () => void
  actions?: ReactNode
}

/** Right-hand sheet on the employer feed: the whole profile, scrolling under a fixed footer. */
export function CandidatePanel({ match, onClose, actions }: Props) {
  const { candidate, matchScore, profileStrength, reasons, matched } = match
  const notes = vacancyNotes(reasons)
  const titleId = useId()
  const photo = useCandidatePhoto(candidate.id, candidate.hasPhoto === true)
  const about = candidate.about?.split('\n\n').filter(Boolean) ?? []

  return (
    <Sheet label="Кандидат" labelledBy={titleId} onClose={onClose} footer={actions}>
      <div className="candidate-panel__person">
        <Avatar name={candidate.displayName} src={photo.data} size="xl" />
        <div className="candidate-panel__titles">
          <h2 id={titleId} className="candidate-panel__title">
            {candidate.displayName}
          </h2>
          {candidate.headline && <p className="candidate-panel__headline">{candidate.headline}</p>}
          {matched && (
            <p className="candidate-panel__matched">Взаимно: кандидат отметил вашу вакансию</p>
          )}
        </div>
      </div>

      <div className="candidate-panel__meters">
        <MatchMeter value={matchScore} label="Под вакансию" />
        <MatchMeter value={profileStrength} label="Сила профиля" />
      </div>

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
        {candidate.englishLevel && (
          <li className="match-card__fact">Английский: {candidate.englishLevel}</li>
        )}
      </ul>

      <CandidateResumes candidate={candidate} />

      {candidate.stack.length > 0 && (
        <SheetSection title="Стек">
          <ChipList items={candidate.stack} label="Стек" />
        </SheetSection>
      )}
      {candidate.softSkills.length > 0 && (
        <SheetSection title="Софт-скиллы">
          <ChipList items={candidate.softSkills} label="Софт-скиллы" />
        </SheetSection>
      )}
      {notes.length > 0 && (
        <SheetSection title="К вакансии">
          <ul>
            {notes.map((note) => (
              <li key={note}>{note}</li>
            ))}
          </ul>
        </SheetSection>
      )}
      {about.length > 0 && (
        <SheetSection title="О себе">
          {about.map((block) => (
            <p key={block}>{block}</p>
          ))}
        </SheetSection>
      )}
      <SheetSection title="Достижения ФСП">
        {candidate.fspAchievements.length > 0 ? (
          <ul>
            {candidate.fspAchievements.map((item) => (
              <li key={`${item.eventName}-${item.year}-${item.discipline}`}>
                {achievementLine(item)}
              </li>
            ))}
          </ul>
        ) : (
          <p className="candidate-panel__none">Нет подтверждённой истории участия в ФСП</p>
        )}
      </SheetSection>

      {candidate.contacts ? (
        <p className="sheet-note">
          Контакты: {candidate.contacts.email}
          {candidate.contacts.phone ? ` · ${candidate.contacts.phone}` : ''}
          {candidate.contacts.telegram ? ` · ${candidate.contacts.telegram}` : ''}
        </p>
      ) : (
        <p className="sheet-note">Контакты откроются после принятия приглашения</p>
      )}
    </Sheet>
  )
}
