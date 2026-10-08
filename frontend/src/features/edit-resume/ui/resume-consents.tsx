import { FSP_SYNC_LABELS } from '@/entities/candidate'
import type { FspSync } from '@/entities/candidate'

export type ConsentValues = {
  personalData: boolean
  profileDisplay: boolean
  fspSync: FspSync | null
}

export const EMPTY_CONSENTS: ConsentValues = {
  personalData: false,
  profileDisplay: false,
  fspSync: null,
}

export const consentsGiven = (values: ConsentValues) =>
  values.personalData && values.profileDisplay && values.fspSync !== null

const FSP_OPTIONS: FspSync[] = ['yes', 'later', 'never']

/** Start of a new resume: both consents and the FSP question come before any data. */
export function ResumeConsents({
  values,
  onChange,
}: {
  values: ConsentValues
  onChange: (next: ConsentValues) => void
}) {
  const set = <K extends keyof ConsentValues>(key: K, value: ConsentValues[K]) =>
    onChange({ ...values, [key]: value })

  return (
    <div className="consents">
      <label className="consents__item">
        <input
          type="checkbox"
          checked={values.personalData}
          onChange={(event) => set('personalData', event.target.checked)}
        />
        <span>
          Согласен на обработку персональных данных по 152-ФЗ: платформа хранит резюме и показывает
          его в подборке.
        </span>
      </label>
      <label className="consents__item">
        <input
          type="checkbox"
          checked={values.profileDisplay}
          onChange={(event) => set('profileDisplay', event.target.checked)}
        />
        <span>
          Согласен, что работодатели увидят профиль без контактов. Телефон и Telegram откроются
          только после принятого приглашения или отклика.
        </span>
      </label>

      <fieldset className="check-group">
        <legend className="check-group__legend">Синхронизировать с ФСП?</legend>
        <div className="check-group__options">
          {FSP_OPTIONS.map((option) => (
            <label key={option} className="check">
              <input
                type="radio"
                name="fsp-sync"
                checked={values.fspSync === option}
                onChange={() => set('fspSync', option)}
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
    </div>
  )
}
