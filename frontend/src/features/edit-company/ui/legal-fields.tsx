import { TextField } from '@/shared/ui'
import type { LegalErrors, LegalValues } from '../model/schema'

export const LEGAL_FIELD_IDS: Record<keyof LegalValues, string> = {
  inn: 'company-inn',
  ogrn: 'company-ogrn',
  kpp: 'company-kpp',
  legalAddress: 'company-address',
}

type Props = {
  values: LegalValues
  errors: LegalErrors
  onChange: (key: keyof LegalValues, value: string) => void
}

/** INN and legal details. Typed by hand: the lookup by INN is not connected yet. */
export function LegalFields({ values, errors, onChange }: Props) {
  const soleTrader = values.inn.replace(/\s+/g, '').length === 12
  return (
    <>
      <div>
        <TextField
          id={LEGAL_FIELD_IDS.inn}
          label="ИНН"
          inputMode="numeric"
          maxLength={14}
          value={values.inn}
          error={errors.inn}
          onChange={(event) => onChange('inn', event.target.value)}
        />
        <p className="form-hint">Автозаполнение по ИНН — в разработке, данные вводятся вручную.</p>
      </div>
      <TextField
        id={LEGAL_FIELD_IDS.ogrn}
        label={soleTrader ? 'ОГРНИП' : 'ОГРН'}
        inputMode="numeric"
        maxLength={17}
        value={values.ogrn}
        error={errors.ogrn}
        onChange={(event) => onChange('ogrn', event.target.value)}
      />
      {!soleTrader && (
        <TextField
          id={LEGAL_FIELD_IDS.kpp}
          label="КПП"
          inputMode="numeric"
          maxLength={11}
          value={values.kpp}
          error={errors.kpp}
          onChange={(event) => onChange('kpp', event.target.value)}
        />
      )}
      <div className="company-form__wide">
        <TextField
          id={LEGAL_FIELD_IDS.legalAddress}
          label="Юридический адрес"
          autoComplete="street-address"
          maxLength={500}
          value={values.legalAddress}
          error={errors.legalAddress}
          onChange={(event) => onChange('legalAddress', event.target.value)}
        />
      </div>
    </>
  )
}
