import type { QuizAnswerDto, QuizTaskDto } from '@/entities/assessment'
import './quiz-question.css'

type Props = {
  task: QuizTaskDto
  /** Positions of the chosen options; null until the candidate picks one. */
  answer: QuizAnswerDto | null
  disabled?: boolean
  onChange: (answer: QuizAnswerDto) => void
}

/** One question with shuffled options; a multiple-choice question allows several answers. */
export function QuizQuestion({ task, answer, disabled, onChange }: Props) {
  const { options, multiple } = task.content
  const selected = answer?.selected ?? []

  const toggle = (position: number) => {
    if (!multiple) return onChange({ selected: [position] })
    onChange({
      selected: selected.includes(position)
        ? selected.filter((item) => item !== position)
        : [...selected, position],
    })
  }

  return (
    <fieldset className="quiz" disabled={disabled}>
      <legend className="quiz__question">{task.statement}</legend>
      {multiple && <p className="quiz__hint">Можно выбрать несколько вариантов</p>}
      <div className="quiz__options">
        {options.map((option, position) => (
          // Options have no ids of their own: the position in this attempt is their identity.
          // oxlint-disable-next-line react/no-array-index-key
          <label key={position} className="quiz__option">
            <input
              type={multiple ? 'checkbox' : 'radio'}
              name={`quiz-${task.id}`}
              checked={selected.includes(position)}
              onChange={() => toggle(position)}
            />
            <span>{option}</span>
          </label>
        ))}
      </div>
    </fieldset>
  )
}
