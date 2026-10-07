import {
  useCallback,
  useEffect,
  useId,
  useRef,
  useState,
  type CSSProperties,
  type ReactNode,
} from 'react'
import { AssessmentStatusBadge } from '@/entities/assessment'
import { CandidateResumes, FSP_DISCIPLINE_LABELS, useCandidatePhoto } from '@/entities/candidate'
import type { CandidateMatchDto, FspAchievementDto } from '@/entities/candidate'
import { WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { useSheetWidth } from '@/shared/lib'
import { MatchMeter } from '@/shared/ui'
import './candidate-sheet.css'

const rub = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

const FSP_LEVELS = {
  regional: 'региональный',
  national: 'всероссийский',
  international: 'международный',
} as const

function initials(name: string) {
  return name
    .split(' ')
    .map((part) => part[0] ?? '')
    .join('')
    .slice(0, 2)
}

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

/** Right-hand sheet on the employer feed. Sized to the screen; a long bio fades instead of scrolling. */
export function CandidatePanel({ match, onClose, actions }: Props) {
  const { candidate, matchScore, profileStrength, reasons, matched } = match
  const notes = vacancyNotes(reasons)
  const titleId = useId()
  const [panelRef, sheet] = useSheetWidth(
    `${candidate.id}:${candidate.about?.length ?? 0}:${candidate.fspAchievements.length}:${candidate.stack.length}:${notes.length}`,
  )
  const closeRef = useRef<HTMLButtonElement>(null)
  const copyRef = useRef<HTMLDivElement>(null)
  const [clipped, setClipped] = useState(false)
  const [leaving, setLeaving] = useState(false)
  const about = candidate.about?.split('\n\n').filter(Boolean) ?? []

  const requestClose = useCallback(() => {
    if (leaving) return
    const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduceMotion) {
      onClose()
      return
    }
    setLeaving(true)
  }, [leaving, onClose])

  useEffect(() => {
    closeRef.current?.focus()
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') requestClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [requestClose])

  useEffect(() => {
    if (!leaving) return
    const timer = window.setTimeout(onClose, 700)
    return () => window.clearTimeout(timer)
  }, [leaving, onClose])

  useEffect(() => {
    const element = copyRef.current
    if (!element || sheet < 0) return
    const measure = () => setClipped(element.scrollHeight > element.clientHeight + 1)
    measure()
    if (typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [sheet])

  return (
    <>
      <button
        type="button"
        className={leaving ? 'candidate-panel__scrim is-leaving' : 'candidate-panel__scrim'}
        aria-label="Закрыть"
        onClick={requestClose}
      />
      <aside
        ref={panelRef}
        className={leaving ? 'candidate-panel is-leaving' : 'candidate-panel'}
        style={{ '--sheet': `${sheet}vw` } as CSSProperties}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        onAnimationEnd={(event) => {
          if (
            event.target === event.currentTarget &&
            leaving &&
            event.animationName === 'candidate-panel-out'
          ) {
            onClose()
          }
        }}
      >
        <header className="candidate-panel__bar">
          <p className="candidate-panel__label">Кандидат</p>
          <button
            ref={closeRef}
            type="button"
            className="candidate-panel__close"
            onClick={requestClose}
          >
            Закрыть
          </button>
        </header>
        <div className="candidate-panel__body">
          <div className="candidate-panel__facts" data-fit="">
            <div className="candidate-panel__person">
              <CandidateAvatar
                candidateId={candidate.id}
                hasPhoto={candidate.hasPhoto === true}
                name={candidate.displayName}
              />
              <div>
                <h2 id={titleId} className="candidate-panel__title">
                  {candidate.displayName}
                </h2>
                {candidate.headline && (
                  <p className="candidate-panel__headline">{candidate.headline}</p>
                )}
                {matched && (
                  <p className="candidate-panel__meta">Взаимно: кандидат отметил вашу вакансию</p>
                )}
              </div>
            </div>
            <div className="match-card__meters">
              {matchScore !== null && <MatchMeter value={matchScore} label="Под вакансию" />}
              <MatchMeter value={profileStrength} label="Сила профиля" />
            </div>
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
              {candidate.englishLevel && (
                <li className="match-card__fact">Английский: {candidate.englishLevel}</li>
              )}
            </ul>
            <CandidateResumes candidate={candidate} />
            {candidate.stack.length > 0 && (
              <ul className="candidate-panel__skills" data-fit="" aria-label="Стек">
                {candidate.stack.map((skill) => (
                  <li key={skill}>{skill}</li>
                ))}
              </ul>
            )}
            {candidate.softSkills.length > 0 && (
              <>
                <p className="candidate-panel__label">Софт-скиллы</p>
                <ul className="candidate-panel__skills" data-fit="" aria-label="Софт-скиллы">
                  {candidate.softSkills.map((skill) => (
                    <li key={skill}>{skill}</li>
                  ))}
                </ul>
              </>
            )}
          </div>
          <div
            ref={copyRef}
            data-fit=""
            className={clipped ? 'candidate-panel__copy is-clipped' : 'candidate-panel__copy'}
          >
            {notes.length > 0 && (
              <section aria-label="К вакансии">
                <p className="candidate-panel__label">К вакансии</p>
                <ul className="candidate-panel__fsp">
                  {notes.map((note) => (
                    <li key={note}>{note}</li>
                  ))}
                </ul>
              </section>
            )}
            {about.length > 0 && (
              <section aria-label="О себе">
                <p className="candidate-panel__label">О себе</p>
                {about.map((block) => (
                  <p key={block}>{block}</p>
                ))}
              </section>
            )}
            <section aria-label="Достижения ФСП">
              <p className="candidate-panel__label">Достижения ФСП</p>
              {candidate.fspAchievements.length > 0 ? (
                <ul className="candidate-panel__fsp">
                  {candidate.fspAchievements.map((item) => (
                    <li key={`${item.eventName}-${item.year}-${item.discipline}`}>
                      {achievementLine(item)}
                    </li>
                  ))}
                </ul>
              ) : (
                <p className="candidate-panel__meta">Нет подтверждённой истории участия в ФСП</p>
              )}
            </section>
            {candidate.contacts ? (
              <p className="candidate-panel__meta">
                Контакты: {candidate.contacts.email}
                {candidate.contacts.phone ? ` · ${candidate.contacts.phone}` : ''}
                {candidate.contacts.telegram ? ` · ${candidate.contacts.telegram}` : ''}
              </p>
            ) : (
              <p className="candidate-panel__meta">Контакты откроются после принятия приглашения</p>
            )}
          </div>
        </div>
        {actions && <footer className="candidate-panel__foot">{actions}</footer>}
      </aside>
    </>
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
  if (photo.data) return <img className="candidate-panel__photo" src={photo.data} alt="" />
  return (
    <span className="candidate-panel__avatar" aria-hidden="true">
      {initials(name)}
    </span>
  )
}
