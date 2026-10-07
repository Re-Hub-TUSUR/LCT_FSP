import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { companyApi, companyKeys } from '@/entities/company'
import type { CompanyDto } from '@/entities/company'
import { getErrorMessage } from '@/shared/api'
import { Button, SelectField, TextArea, TextField } from '@/shared/ui'
import {
  COMPANY_SIZES,
  DESCRIPTION_MAX,
  DESCRIPTION_MIN,
  INDUSTRIES,
  companyValuesFrom,
  toCompanyPayload,
  validateCompany,
} from '../model/schema'
import type { CompanyErrors, CompanyValues, LegalValues } from '../model/schema'
import { LEGAL_FIELD_IDS, LegalFields } from './legal-fields'
import { LogoField } from './logo-field'
import './company-form.css'

const FIELD_IDS: Record<keyof CompanyValues, string> = {
  ...LEGAL_FIELD_IDS,
  name: 'company-name',
  industry: 'company-industry',
  description: 'company-description',
  city: 'company-city',
  size: 'company-size',
  website: 'company-website',
  contactEmail: 'company-email',
}

type Props = {
  company: CompanyDto | null
  /** Legal details from the previous setup step; the form then shows the public profile only. */
  legal?: LegalValues
  onSaved?: (company: CompanyDto) => void
  onBack?: () => void
}

export function CompanyForm({ company, legal, onSaved, onBack }: Props) {
  const queryClient = useQueryClient()
  const [values, setValues] = useState<CompanyValues>(() => ({
    ...companyValuesFrom(company),
    ...legal,
  }))
  const [errors, setErrors] = useState<CompanyErrors>({})
  const [formError, setFormError] = useState('')
  const [saved, setSaved] = useState(false)

  const save = useMutation({
    mutationFn: companyApi.save,
    onSuccess: (next) => {
      onSaved?.(next)
      queryClient.setQueryData(companyKeys.mine(), next)
      setSaved(true)
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const update = <K extends keyof CompanyValues>(key: K, value: CompanyValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    setSaved(false)
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextErrors = validateCompany(values)
    setErrors(nextErrors)
    const first = (Object.keys(FIELD_IDS) as (keyof CompanyValues)[]).find((key) => nextErrors[key])
    if (first) {
      if (legal && first in LEGAL_FIELD_IDS) {
        setFormError(`${nextErrors[first]}: вернитесь на шаг «Компания»`)
        return
      }
      document.getElementById(FIELD_IDS[first])?.focus()
      return
    }
    save.mutate(toCompanyPayload(values))
  }

  const length = values.description.trim().length

  return (
    <form className="company-form" noValidate onSubmit={onSubmit}>
      {!legal && (
        <fieldset className="company-form__group">
          <legend className="company-form__legend">Реквизиты</legend>
          <div className="company-form__grid">
            <LegalFields values={values} errors={errors} onChange={update} />
          </div>
        </fieldset>
      )}
      <fieldset className="company-form__group">
        <legend className="company-form__legend">Профиль для кандидатов</legend>
        <div className="company-form__grid">
          <div>
            <TextField
              id="company-name"
              label="Название для кандидатов"
              autoComplete="organization"
              value={values.name}
              error={errors.name}
              onChange={(event) => update('name', event.target.value)}
            />
            <p className="form-hint">Можно короче юридического: «Технологии», а не ООО «…».</p>
          </div>
          <div>
            <TextField
              id="company-industry"
              label="Направление деятельности"
              value={values.industry}
              error={errors.industry}
              onChange={(event) => update('industry', event.target.value)}
            />
            <p className="form-hint">Например: {INDUSTRIES.slice(0, 4).join(', ')}</p>
          </div>
          <TextField
            id="company-city"
            label="Город"
            autoComplete="address-level2"
            value={values.city}
            error={errors.city}
            onChange={(event) => update('city', event.target.value)}
          />
          <SelectField
            id="company-size"
            label="Размер компании"
            value={values.size}
            error={errors.size}
            onChange={(event) => update('size', event.target.value)}
          >
            {COMPANY_SIZES.map((item) => (
              <option key={item.value || 'empty'} value={item.value}>
                {item.label}
              </option>
            ))}
          </SelectField>
          <TextField
            id="company-website"
            label="Сайт"
            inputMode="url"
            autoComplete="url"
            placeholder="company.ru"
            value={values.website}
            error={errors.website}
            onChange={(event) => update('website', event.target.value)}
          />
          <TextField
            id="company-email"
            label="Контакт для кандидатов"
            type="email"
            autoComplete="email"
            value={values.contactEmail}
            error={errors.contactEmail}
            onChange={(event) => update('contactEmail', event.target.value)}
          />
          <div className="company-form__wide">
            <TextArea
              id="company-description"
              label="Описание"
              maxLength={DESCRIPTION_MAX}
              value={values.description}
              error={errors.description}
              onChange={(event) => update('description', event.target.value)}
            />
            <p className="form-hint">
              {length} / {DESCRIPTION_MAX}
              {length < DESCRIPTION_MIN ? ` · минимум ${DESCRIPTION_MIN}` : ''}
            </p>
          </div>
        </div>
      </fieldset>
      {company && <LogoField company={company} />}
      {formError && (
        <p className="form-banner" role="alert">
          {formError}
        </p>
      )}
      {saved && !onSaved && (
        <p className="form-status" role="status">
          Профиль компании сохранён.
        </p>
      )}

      <div className="form-actions">
        {onBack && (
          <Button type="button" variant="ghost" size="inline" onClick={onBack}>
            Назад
          </Button>
        )}
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : onSaved ? 'Сохранить и продолжить' : 'Сохранить'}
        </Button>
      </div>
    </form>
  )
}
