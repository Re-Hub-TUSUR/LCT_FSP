import { Button, TextField } from '@/shared/ui'
import { EMPTY_EXPERIENCE, experienceYearsOf } from '../model/schema'
import type { ExperienceRow } from '../model/schema'

type Props = {
  rows: ExperienceRow[]
  noExperience: boolean
  years: string
  error?: string
  yearsError?: string
  onRows: (rows: ExperienceRow[]) => void
  onNoExperience: (value: boolean) => void
  onYears: (value: string) => void
}

const MAX_ROWS = 30

/** Places of work by month; total years come from the periods, overlaps count once. */
export function ExperienceField({
  rows,
  noExperience,
  years,
  error,
  yearsError,
  onRows,
  onNoExperience,
  onYears,
}: Props) {
  const change = (index: number, patch: Partial<ExperienceRow>) =>
    onRows(rows.map((row, at) => (at === index ? { ...row, ...patch } : row)))

  return (
    <fieldset className="check-group resume-form__wide experience">
      <legend className="check-group__legend">Опыт работы</legend>
      <label className="check">
        <input
          id="resume-no-experience"
          type="checkbox"
          checked={noExperience}
          onChange={(event) => onNoExperience(event.target.checked)}
        />
        Нет опыта
      </label>

      {!noExperience && (
        <>
          {rows.length === 0 ? (
            <div className="experience__years">
              <TextField
                id="resume-experience"
                label="Стаж, лет"
                inputMode="numeric"
                value={years}
                error={yearsError}
                onChange={(event) => onYears(event.target.value)}
              />
            </div>
          ) : (
            <p className="form-hint">
              По периодам: {experienceYearsOf(rows)} полных лет. Пересекающиеся месяцы считаются
              один раз.
            </p>
          )}

          <ol className="experience__list">
            {rows.map((row, index) => (
              // Rows have no identity of their own; the order is the identity while editing.
              // oxlint-disable-next-line react/no-array-index-key
              <li key={index} className="experience__row">
                <TextField
                  id={`experience-${index}-company`}
                  label="Компания"
                  value={row.company}
                  onChange={(event) => change(index, { company: event.target.value })}
                />
                <TextField
                  id={`experience-${index}-position`}
                  label="Должность"
                  value={row.position}
                  onChange={(event) => change(index, { position: event.target.value })}
                />
                <TextField
                  id={`experience-${index}-start`}
                  label="Начало"
                  type="month"
                  placeholder="2023-09"
                  value={row.start}
                  onChange={(event) => change(index, { start: event.target.value })}
                />
                <TextField
                  id={`experience-${index}-end`}
                  label="Окончание (пусто — работаю сейчас)"
                  type="month"
                  placeholder="2025-06"
                  value={row.end}
                  onChange={(event) => change(index, { end: event.target.value })}
                />
                <div className="experience__wide">
                  <TextField
                    id={`experience-${index}-stack`}
                    label="Стек на этом месте, через запятую"
                    value={row.stack}
                    onChange={(event) => change(index, { stack: event.target.value })}
                  />
                </div>
                <div className="experience__wide">
                  <Button
                    type="button"
                    variant="ghost"
                    size="inline"
                    onClick={() => onRows(rows.filter((_, at) => at !== index))}
                  >
                    Удалить место работы
                  </Button>
                </div>
              </li>
            ))}
          </ol>

          {rows.length < MAX_ROWS && (
            <div className="form-actions">
              <Button
                type="button"
                variant="ghost"
                size="inline"
                onClick={() => onRows([...rows, EMPTY_EXPERIENCE])}
              >
                Добавить место работы
              </Button>
            </div>
          )}
        </>
      )}
      {error && (
        <p id="resume-experience-list-error" className="check-group__error" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  )
}
