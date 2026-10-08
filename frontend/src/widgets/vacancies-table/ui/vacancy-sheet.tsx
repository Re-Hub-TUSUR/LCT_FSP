import { useId } from 'react'
import { GRADE_LABELS } from '@/entities/category'
import {
  BENEFIT_LABELS,
  EMPLOYMENT_LABELS,
  FSP_RESULT_LABELS,
  SALARY_NOTE,
  WORK_FORMAT_LABELS,
} from '@/entities/vacancy'
import type { VacancyDto } from '@/entities/vacancy'
import { paths, ROUTES } from '@/shared/config'
import { formatDate, formatRubRange } from '@/shared/lib'
import { ButtonLink, Sheet, SheetSection, VerifiedMark } from '@/shared/ui'

const EXPERIENCE: Record<number, string> = {
  0: 'Без опыта',
  1: 'Опыт от года',
  3: 'Опыт от 3 лет',
  5: 'Опыт от 5 лет',
}

/** «Без опыта» is said only for entry grades: elsewhere a zero just means «not specified». */
function experienceFact(vacancy: VacancyDto): string | null {
  const years = vacancy.minExperienceYears
  if (years === null) return null
  if (years === 0 && !vacancy.grades.some((grade) => grade === 'intern' || grade === 'junior')) {
    return null
  }
  return EXPERIENCE[years] ?? `Опыт от ${years} лет`
}

type Props = {
  vacancy: VacancyDto
  /** The viewer's company owns it: the sheet offers to pick candidates for it and to edit it. */
  own: boolean
  onClose: () => void
}

/** The whole vacancy on the side sheet: facts, description, stack and conditions. */
export function VacancySheet({ vacancy, own, onClose }: Props) {
  const titleId = useId()
  const blocks = vacancy.description.split('\n\n').filter(Boolean)
  // Older vacancies have one flat stack: treat it as required.
  const required = vacancy.stackRequired.length > 0 ? vacancy.stackRequired : vacancy.stack
  const nice = vacancy.stackNice.filter((skill) => !required.includes(skill))

  const facts = [
    WORK_FORMAT_LABELS[vacancy.workFormat],
    vacancy.city,
    vacancy.grades.map((grade) => GRADE_LABELS[grade]).join(' / '),
    ...vacancy.employmentTypes.map((type) => EMPLOYMENT_LABELS[type]),
    experienceFact(vacancy),
  ].filter((fact): fact is string => Boolean(fact))

  const conditions = [
    ...vacancy.benefits.map((benefit) => BENEFIT_LABELS[benefit]),
    vacancy.relocationHelp ? 'Помощь с переездом' : null,
    vacancy.verifiedGradeOnly ? 'Только с грейдом, подтверждённым тестом' : null,
    vacancy.fspBestResult
      ? `Результат ФСП: ${FSP_RESULT_LABELS[vacancy.fspBestResult].toLowerCase()}${
          vacancy.fspDiscipline ? ` · ${vacancy.fspDiscipline}` : ''
        }`
      : null,
  ].filter((line): line is string => Boolean(line))

  return (
    <Sheet
      label="Вакансия"
      labelledBy={titleId}
      onClose={onClose}
      footer={
        own ? (
          <>
            <ButtonLink size="block" to={`${ROUTES.feed}?vacancyId=${vacancy.id}`}>
              Подобрать кандидатов
            </ButtonLink>
            <ButtonLink variant="ghost" size="block" to={paths.vacancyEdit(vacancy.id)}>
              Редактировать
            </ButtonLink>
          </>
        ) : undefined
      }
    >
      <div className="vacancy-sheet__head">
        <p className="vacancy-sheet__company">
          <b>{vacancy.company.name}</b>
          {vacancy.company.itAccredited && <VerifiedMark />}
          {vacancy.company.industry && <span> · {vacancy.company.industry}</span>}
        </p>
        <h2 id={titleId} className="vacancy-sheet__title">
          {vacancy.title}
        </h2>
        <p className="vacancy-sheet__salary">
          {formatRubRange(vacancy.salary.from, vacancy.salary.to)}
          <span> {SALARY_NOTE}</span>
        </p>
      </div>

      <ul className="vacancy-sheet__facts">
        <li className="is-accent">{vacancy.category.label}</li>
        {facts.map((fact) => (
          <li key={fact}>{fact}</li>
        ))}
      </ul>

      {blocks.length > 0 && (
        <SheetSection title="Описание">
          {blocks.map((block) => (
            <p key={block} className="vacancy-sheet__text">
              {block}
            </p>
          ))}
        </SheetSection>
      )}

      {(required.length > 0 || nice.length > 0) && (
        <SheetSection title="Стек">
          <ul className="vacancy-sheet__stack">
            {required.map((skill) => (
              <li key={skill} className="is-required">
                {skill}
              </li>
            ))}
            {nice.map((skill) => (
              <li key={skill}>{skill}</li>
            ))}
          </ul>
        </SheetSection>
      )}

      {conditions.length > 0 && (
        <SheetSection title="Условия и требования">
          <ul>
            {conditions.map((line) => (
              <li key={line}>{line}</li>
            ))}
          </ul>
        </SheetSection>
      )}

      <p className="sheet-note">
        {vacancy.publishedAt
          ? `Опубликована ${formatDate(vacancy.publishedAt)}`
          : 'Черновик: кандидаты эту вакансию пока не видят'}
      </p>
    </Sheet>
  )
}
