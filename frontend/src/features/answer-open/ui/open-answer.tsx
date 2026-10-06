import type { OpenAnswerDto, OpenTaskDto } from '@/entities/assessment'
import { TextArea } from '@/shared/ui'
import './open-answer.css'

type Props = {
  task: OpenTaskDto
  answer: OpenAnswerDto | null
  disabled?: boolean
  onChange: (answer: OpenAnswerDto) => void
  /** Reported for reviewers; never changes the score. */
  onPaste?: () => void
}

/** Free-text answer. The company that sent the test reads and grades it by hand. */
export function OpenAnswer({ task, answer, disabled, onChange, onPaste }: Props) {
  const text = answer?.text ?? ''
  const { maxLength } = task.content

  return (
    <div className="open-answer">
      <h2 className="open-answer__title">{task.title}</h2>
      <p className="open-answer__statement">{task.statement}</p>
      <TextArea
        id={`open-${task.id}`}
        label="Ваш ответ"
        className="open-answer__field"
        value={text}
        maxLength={maxLength}
        disabled={disabled}
        onChange={(e) => onChange({ text: e.target.value })}
        onPaste={onPaste}
      />
      <p className="open-answer__hint">
        {text.length} из {maxLength} символов · ответ проверяет компания, а не автоматика
      </p>
    </div>
  )
}
