import { Button, TextField } from '@/shared/ui'
import { EMPTY_EDUCATION } from '../model/schema'
import type { EducationRow } from '../model/schema'

type Props = {
  rows: EducationRow[]
  error?: string
  onRows: (rows: EducationRow[]) => void
}

const MAX_ROWS = 10

export function EducationField({ rows, error, onRows }: Props) {
  const change = (index: number, patch: Partial<EducationRow>) =>
    onRows(rows.map((row, at) => (at === index ? { ...row, ...patch } : row)))

  return (
    <fieldset className="check-group resume-form__wide experience">
      <legend className="check-group__legend">Образование (необязательно)</legend>
      <ol className="experience__list">
        {rows.map((row, index) => (
          // oxlint-disable-next-line react/no-array-index-key
          <li key={index} className="experience__row">
            <div className="experience__wide">
              <TextField
                id={`education-${index}-institution`}
                label="Учебное заведение"
                value={row.institution}
                onChange={(event) => change(index, { institution: event.target.value })}
              />
            </div>
            <TextField
              id={`education-${index}-specialty`}
              label="Специальность"
              value={row.specialty}
              onChange={(event) => change(index, { specialty: event.target.value })}
            />
            <TextField
              id={`education-${index}-year`}
              label="Год окончания"
              inputMode="numeric"
              maxLength={4}
              value={row.year}
              onChange={(event) => change(index, { year: event.target.value })}
            />
            <div className="experience__wide">
              <Button
                type="button"
                variant="ghost"
                size="inline"
                onClick={() => onRows(rows.filter((_, at) => at !== index))}
              >
                Удалить
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
            onClick={() => onRows([...rows, EMPTY_EDUCATION])}
          >
            Добавить образование
          </Button>
        </div>
      )}
      {error && (
        <p className="check-group__error" role="alert">
          {error}
        </p>
      )}
    </fieldset>
  )
}
