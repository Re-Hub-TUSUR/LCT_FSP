import { TextArea, TextField } from '@/shared/ui'
import type { OpenDraft } from '../../model/kinds'

type Props = {
  draft: OpenDraft
  onChange: (draft: OpenDraft) => void
}

/** A free-text question: how long the answer may be and what the reviewer looks for. */
export function OpenFields({ draft, onChange }: Props) {
  return (
    <>
      <TextField
        id="task-max-length"
        label="Максимальная длина ответа, символов"
        inputMode="numeric"
        value={draft.maxLength}
        onChange={(e) => onChange({ ...draft, maxLength: e.target.value })}
      />
      <TextArea
        id="task-guidance"
        label="На что смотреть при проверке (кандидат этого не видит)"
        value={draft.guidance}
        maxLength={4000}
        onChange={(e) => onChange({ ...draft, guidance: e.target.value })}
      />
      <p className="task-form__legend">
        Ответ на открытый вопрос вы оцениваете сами: итог теста появится после проверки.
      </p>
    </>
  )
}
