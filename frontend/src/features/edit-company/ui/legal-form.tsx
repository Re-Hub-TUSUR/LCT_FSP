import { useState } from 'react'
import type { FormEvent } from 'react'
import { Button } from '@/shared/ui'
import { validateLegal } from '../model/schema'
import type { LegalErrors, LegalValues } from '../model/schema'
import { LEGAL_FIELD_IDS, LegalFields } from './legal-fields'
import './company-form.css'

type Props = {
  initial: LegalValues
  onNext: (values: LegalValues) => void
  onBack?: () => void
}

/** Setup step «Компания»: the legal details, saved together with the public profile. */
export function LegalForm({ initial, onNext, onBack }: Props) {
  const [values, setValues] = useState<LegalValues>(initial)
  const [errors, setErrors] = useState<LegalErrors>({})

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const next = validateLegal(values)
    setErrors(next)
    const first = (Object.keys(LEGAL_FIELD_IDS) as (keyof LegalValues)[]).find((key) => next[key])
    if (first) {
      document.getElementById(LEGAL_FIELD_IDS[first])?.focus()
      return
    }
    onNext(values)
  }

  return (
    <form className="company-form" noValidate onSubmit={onSubmit}>
      <div className="company-form__grid">
        <LegalFields
          values={values}
          errors={errors}
          onChange={(key, value) => {
            setValues((prev) => ({ ...prev, [key]: value }))
            if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
          }}
        />
      </div>
      <div className="form-actions">
        {onBack && (
          <Button type="button" variant="ghost" size="inline" onClick={onBack}>
            Назад
          </Button>
        )}
        <Button type="submit" size="inline">
          Далее
        </Button>
      </div>
    </form>
  )
}
