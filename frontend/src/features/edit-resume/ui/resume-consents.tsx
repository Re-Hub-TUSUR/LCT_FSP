import { FSP_SYNC_LABELS } from '@/entities/candidate'
import type { FspSync } from '@/entities/candidate'

/** The consents were given at registration; the start of a resume asks only about the FSP. */
export type ConsentValues = {
  fspSync: FspSync | null
}

export const EMPTY_CONSENTS: ConsentValues = { fspSync: null }

export const consentsGiven = (values: ConsentValues) => values.fspSync !== null

const FSP_OPTIONS: FspSync[] = ['yes', 'later', 'never']

export function ResumeConsents({
  values,
  onChange,
}: {
  values: ConsentValues
  onChange: (next: ConsentValues) => void
}) {
  return (
    <div className="consents">
      <fieldset className="check-group">
        <legend className="check-group__legend">Синхронизировать с ФСП?</legend>
        <div className="check-group__options">
          {FSP_OPTIONS.map((option) => (
            <label key={option} className="check">
              <input
                type="radio"
                name="fsp-sync"
                checked={values.fspSync === option}
                onChange={() => onChange({ fspSync: option })}
              />
              {FSP_SYNC_LABELS[option]}
            </label>
          ))}
        </div>
      </fieldset>

      {values.fspSync === 'yes' && (
        <p className="form-hint">
          После сохранения резюме привяжите ФСП ID в настройках: вход через ФСП подтвердит номер
          участника, а результаты придут из реестра Федерации. Вводить ID вручную не нужно.
        </p>
      )}
      <p className="form-hint">
        Работодатели увидят профиль без контактов: телефон и Telegram откроются только после
        принятого приглашения или отклика. Скрыть профиль можно статусом поиска «Не ищу».
      </p>
    </div>
  )
}
