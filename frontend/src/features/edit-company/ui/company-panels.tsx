import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { companyApi, companyKeys } from '@/entities/company'
import type { CompanyDto } from '@/entities/company'
import { getErrorMessage } from '@/shared/api'
import { Button, DataRows, Panel, SelectField, TextArea, TextField } from '@/shared/ui'
import {
  COMPANY_SIZES,
  DESCRIPTION_MAX,
  DESCRIPTION_MIN,
  INDUSTRIES,
  companyValuesFrom,
  toCompanyPayload,
  validateCompany,
} from '../model/schema'
import type { CompanyErrors, CompanyValues } from '../model/schema'
import { LEGAL_FIELD_IDS, LegalFields } from './legal-fields'
import { LogoField } from './logo-field'
import './company-form.css'

export type CompanyPanelId = 'legal' | 'profile' | 'description'

const PANELS: CompanyPanelId[] = ['legal', 'profile', 'description']

const TITLES: Record<CompanyPanelId, string> = {
  legal: 'Реквизиты',
  profile: 'Профиль для кандидатов',
  description: 'Описание',
}

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

export const COMPANY_PANEL_FIELDS: Record<CompanyPanelId, (keyof CompanyValues)[]> = {
  legal: ['inn', 'ogrn', 'kpp', 'legalAddress'],
  profile: ['name', 'industry', 'city', 'size', 'website', 'contactEmail'],
  description: ['description'],
}

/** PUT /companies/me takes the whole profile, so only the errors of the open panel are shown. */
export function validateCompanyPanel(values: CompanyValues, panel: CompanyPanelId): CompanyErrors {
  const all = validateCompany(values)
  const errors: CompanyErrors = {}
  for (const field of COMPANY_PANEL_FIELDS[panel]) {
    if (all[field]) errors[field] = all[field]
  }
  return errors
}

function sizeLabel(size: string | null): string | null {
  if (!size) return null
  return COMPANY_SIZES.find((item) => item.value === size)?.label ?? size
}

/** Saved company as read-only panels; «Изменить» opens one panel's form in place. */
export function CompanyPanels({ company }: { company: CompanyDto }) {
  const queryClient = useQueryClient()
  const [editing, setEditing] = useState<CompanyPanelId | null>(null)
  const [values, setValues] = useState<CompanyValues>(() => companyValuesFrom(company))
  const [errors, setErrors] = useState<CompanyErrors>({})
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')

  const save = useMutation({
    mutationFn: companyApi.save,
    onSuccess: (next) => {
      queryClient.setQueryData(companyKeys.mine(), next)
      setValues(companyValuesFrom(next))
      setEditing(null)
      setErrors({})
      setFormError('')
      setNotice('Сохранено.')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const update = <K extends keyof CompanyValues>(key: K, value: CompanyValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const open = (panel: CompanyPanelId) => {
    setValues(companyValuesFrom(company))
    setEditing(panel)
    setErrors({})
    setFormError('')
    setNotice('')
  }

  const cancel = () => {
    setValues(companyValuesFrom(company))
    setEditing(null)
    setErrors({})
    setFormError('')
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (!editing) return
    const next = validateCompanyPanel(values, editing)
    setErrors(next)
    const first = COMPANY_PANEL_FIELDS[editing].find((field) => next[field])
    if (first) {
      document.getElementById(FIELD_IDS[first])?.focus()
      return
    }
    const rest = validateCompany(values)
    const elsewhere = (Object.keys(rest) as (keyof CompanyValues)[]).find(
      (field) => !COMPANY_PANEL_FIELDS[editing].includes(field),
    )
    if (elsewhere) {
      const panel = PANELS.find((item) => COMPANY_PANEL_FIELDS[item].includes(elsewhere))
      setFormError(
        `Сначала поправьте раздел «${panel ? TITLES[panel] : ''}»: ${rest[elsewhere] ?? ''}`,
      )
      return
    }
    save.mutate(toCompanyPayload(values))
  }

  const length = values.description.trim().length

  const read: Record<CompanyPanelId, ReactNode> = {
    legal: (
      <DataRows
        rows={[
          { key: 'inn', label: 'ИНН', value: company.inn },
          {
            key: 'ogrn',
            label: company.inn?.length === 12 ? 'ОГРНИП' : 'ОГРН',
            value: company.ogrn,
          },
          ...(company.inn?.length === 12 ? [] : [{ key: 'kpp', label: 'КПП', value: company.kpp }]),
          { key: 'address', label: 'Юридический адрес', value: company.legalAddress },
        ]}
      />
    ),
    profile: (
      <DataRows
        rows={[
          { key: 'name', label: 'Название', value: company.name },
          { key: 'industry', label: 'Направление', value: company.industry },
          { key: 'city', label: 'Город', value: company.city },
          { key: 'size', label: 'Размер', value: sizeLabel(company.size) },
          { key: 'site', label: 'Сайт', value: company.website },
          {
            key: 'email',
            label: 'Контакт для кандидатов',
            value: company.contactEmail,
            note: 'Кандидат видит его в приглашении.',
          },
        ]}
      />
    ),
    description: company.description ? (
      <p className="company-panels__text">{company.description}</p>
    ) : (
      <p className="company-panels__text company-panels__text--dim">
        Расскажите, чем занимается компания и какие задачи ждут специалиста.
      </p>
    ),
  }

  const fields: Record<CompanyPanelId, ReactNode> = {
    legal: (
      <div className="company-form__grid">
        <LegalFields values={values} errors={errors} onChange={update} />
      </div>
    ),
    profile: (
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
          <SelectField
            id="company-industry"
            label="Направление деятельности"
            value={values.industry}
            error={errors.industry}
            onChange={(event) => update('industry', event.target.value)}
          >
            <option value="">Выберите направление</option>
            {INDUSTRIES.map((industry) => (
              <option key={industry} value={industry}>
                {industry}
              </option>
            ))}
          </SelectField>
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
      </div>
    ),
    description: (
      <div>
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
    ),
  }

  return (
    <div className="company-panels">
      {notice && (
        <p className="form-status" role="status">
          {notice}
        </p>
      )}
      {PANELS.map((panel) => (
        <Panel
          key={panel}
          title={TITLES[panel]}
          className={editing === panel ? 'is-editing' : undefined}
          action={
            editing === null ? (
              <button type="button" className="panel-edit" onClick={() => open(panel)}>
                Изменить
              </button>
            ) : undefined
          }
        >
          {editing === panel ? (
            <form className="company-form" noValidate onSubmit={onSubmit}>
              {fields[panel]}
              {formError && (
                <p className="form-banner" role="alert">
                  {formError}
                </p>
              )}
              <div className="form-actions">
                <Button type="submit" size="inline" disabled={save.isPending}>
                  {save.isPending ? 'Сохраняем…' : 'Сохранить'}
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="inline"
                  disabled={save.isPending}
                  onClick={cancel}
                >
                  Отмена
                </Button>
              </div>
            </form>
          ) : (
            read[panel]
          )}
        </Panel>
      ))}
      <Panel title="Логотип">
        <LogoField company={company} />
      </Panel>
    </div>
  )
}
