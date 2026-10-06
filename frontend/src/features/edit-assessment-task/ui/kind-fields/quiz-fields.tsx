import { Button, TextField } from '@/shared/ui'
import type { QuizDraft } from '../../model/kinds'

type Props = {
  draft: QuizDraft
  onChange: (draft: QuizDraft) => void
}

/** Options of a choice question with the mark of the correct ones. */
export function QuizFields({ draft, onChange }: Props) {
  const setOption = (index: number, text: string) =>
    onChange({
      ...draft,
      options: draft.options.map((option, position) => (position === index ? text : option)),
    })

  const removeOption = (index: number) =>
    onChange({
      ...draft,
      options: draft.options.filter((_, position) => position !== index),
      // Indexes after the removed option shift down by one.
      correct: draft.correct
        .filter((position) => position !== index)
        .map((position) => (position > index ? position - 1 : position)),
    })

  const markCorrect = (index: number) =>
    onChange({
      ...draft,
      correct: !draft.multiple
        ? [index]
        : draft.correct.includes(index)
          ? draft.correct.filter((position) => position !== index)
          : [...draft.correct, index],
    })

  return (
    <fieldset className="task-form__group">
      <legend>Варианты ответа — отметьте верный</legend>
      <label className="task-form__check">
        <input
          type="checkbox"
          checked={draft.multiple}
          onChange={(e) =>
            onChange({
              ...draft,
              multiple: e.target.checked,
              correct: e.target.checked ? draft.correct : draft.correct.slice(0, 1),
            })
          }
        />
        <span>Несколько верных вариантов</span>
      </label>
      {draft.options.map((option, index) => (
        // Rows are edited in place and have no id until saved.
        // oxlint-disable-next-line react/no-array-index-key
        <div key={index} className="task-form__option">
          <input
            type={draft.multiple ? 'checkbox' : 'radio'}
            name="task-correct"
            aria-label={`Вариант ${index + 1} верный`}
            checked={draft.correct.includes(index)}
            onChange={() => markCorrect(index)}
          />
          <TextField
            id={`task-option-${index}`}
            label={`Вариант ${index + 1}`}
            hideLabel
            placeholder={`Вариант ${index + 1}`}
            value={option}
            maxLength={500}
            onChange={(e) => setOption(index, e.target.value)}
          />
          <Button
            variant="ghost"
            size="inline"
            disabled={draft.options.length <= 2}
            aria-label={`Удалить вариант ${index + 1}`}
            onClick={() => removeOption(index)}
          >
            Удалить
          </Button>
        </div>
      ))}
      <Button
        variant="ghost"
        size="inline"
        disabled={draft.options.length >= 8}
        onClick={() => onChange({ ...draft, options: [...draft.options, ''] })}
      >
        Добавить вариант
      </Button>
    </fieldset>
  )
}
