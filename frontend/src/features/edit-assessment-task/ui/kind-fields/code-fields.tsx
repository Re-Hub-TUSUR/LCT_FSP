import { useState } from 'react'
import { LANGUAGES } from '@/entities/assessment'
import type { TestGroupDto } from '@/entities/assessment'
import { Button, Chip, CodeEditor, SelectField, TextArea, TextField } from '@/shared/ui'
import { MAX_EXPECTED_OUTPUT } from '../../model/kinds'
import type { CodeDraft } from '../../model/kinds'

type Props = {
  draft: CodeDraft
  onChange: (draft: CodeDraft) => void
}

/** Test groups, limits, languages and the reference solution of a code task. */
export function CodeFields({ draft, onChange }: Props) {
  const set = (patch: Partial<CodeDraft>) => onChange({ ...draft, ...patch })
  const [starterLanguage, setStarterLanguage] = useState(
    () => Object.keys(draft.starter)[0] ?? draft.referenceLanguage,
  )

  const setGroup = (index: number, patch: Partial<TestGroupDto>) =>
    set({
      groups: draft.groups.map((group, position) =>
        position === index ? { ...group, ...patch } : group,
      ),
    })

  return (
    <>
      <fieldset className="task-form__group">
        <legend>
          Группы тестов: один запуск программы на группу, вывод до {MAX_EXPECTED_OUTPUT} символов
        </legend>
        {draft.groups.map((group, index) => (
          // Rows are edited in place and have no id until saved.
          // oxlint-disable-next-line react/no-array-index-key
          <div key={index} className="task-form__test">
            <TextArea
              id={`task-input-${index}`}
              label={`Группа ${index + 1}: ввод`}
              value={group.input}
              onChange={(e) => setGroup(index, { input: e.target.value })}
            />
            <TextArea
              id={`task-expected-${index}`}
              label="Ожидаемый вывод"
              value={group.expected}
              onChange={(e) => setGroup(index, { expected: e.target.value })}
            />
            <div className="task-form__test-actions">
              <label className="task-form__check">
                <input
                  type="checkbox"
                  checked={group.hidden}
                  onChange={(e) => setGroup(index, { hidden: e.target.checked })}
                />
                <span>Закрытая: кандидат не видит, решает итог</span>
              </label>
              {group.hidden && (
                <TextField
                  id={`task-weight-${index}`}
                  label="Вес в оценке (1–10)"
                  type="number"
                  min={1}
                  max={10}
                  value={String(group.weight ?? 1)}
                  onChange={(e) => setGroup(index, { weight: Number(e.target.value) })}
                />
              )}
              <Button
                variant="ghost"
                size="inline"
                disabled={draft.groups.length <= 2}
                onClick={() =>
                  set({ groups: draft.groups.filter((_, position) => position !== index) })
                }
              >
                Удалить группу
              </Button>
            </div>
          </div>
        ))}
        <Button
          variant="ghost"
          size="inline"
          disabled={draft.groups.length >= 8}
          onClick={() =>
            set({ groups: [...draft.groups, { input: '', expected: '', hidden: true }] })
          }
        >
          Добавить группу
        </Button>
      </fieldset>

      <div className="task-form__row">
        <TextField
          id="task-time-limit"
          label="Ограничение времени, с"
          inputMode="decimal"
          value={draft.timeLimit}
          onChange={(e) => set({ timeLimit: e.target.value })}
        />
        <SelectField
          id="task-reference-language"
          label="Язык эталонного решения"
          value={draft.referenceLanguage}
          onChange={(e) => set({ referenceLanguage: e.target.value })}
        >
          {LANGUAGES.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
            </option>
          ))}
        </SelectField>
      </div>

      <fieldset className="task-form__group">
        <legend>Языки для кандидата (ничего не выбрано — все)</legend>
        <div className="task-form__chips">
          {LANGUAGES.map((item) => (
            <Chip
              key={item.id}
              active={draft.languages.includes(item.id)}
              onClick={() =>
                set({
                  languages: draft.languages.includes(item.id)
                    ? draft.languages.filter((id) => id !== item.id)
                    : [...draft.languages, item.id],
                })
              }
            >
              {item.label}
            </Chip>
          ))}
        </div>
      </fieldset>

      <div className="task-form__group">
        <p className="task-form__legend">
          Эталонное решение — им проверяются тесты перед публикацией
        </p>
        <CodeEditor
          value={draft.referenceCode}
          language={draft.referenceLanguage}
          label="Эталонное решение"
          height="260px"
          onChange={(code) => set({ referenceCode: code })}
        />
      </div>

      <div className="task-form__group">
        <p className="task-form__legend">
          Стартовый код (необязательно) — программа с ошибкой, которую кандидат получит вместо
          пустого редактора. Оценку по-прежнему решают закрытые группы тестов
        </p>
        <SelectField
          id="task-starter-language"
          label="Язык стартового кода"
          value={starterLanguage}
          onChange={(e) => setStarterLanguage(e.target.value)}
        >
          {LANGUAGES.map((item) => (
            <option key={item.id} value={item.id}>
              {item.label}
              {draft.starter[item.id]?.trim() ? ' · заполнен' : ''}
            </option>
          ))}
        </SelectField>
        <CodeEditor
          value={draft.starter[starterLanguage] ?? ''}
          language={starterLanguage}
          label="Стартовый код"
          height="200px"
          onChange={(code) => set({ starter: { ...draft.starter, [starterLanguage]: code } })}
        />
      </div>
    </>
  )
}
