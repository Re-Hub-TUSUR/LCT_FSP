import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import { candidateApi, candidateKeys } from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { categoryQueries } from '@/entities/category'
import { WORK_FORMAT_LABELS, WORK_FORMATS } from '@/entities/vacancy'
import type { WorkFormat } from '@/entities/vacancy'
import { ApiError, getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Button, SelectField, TextArea, TextField } from '@/shared/ui'
import { resumeValuesFrom, toResumePayload, validateResume } from '../model/schema'
import type { ResumeErrors, ResumeValues } from '../model/schema'
import './resume-form.css'

const PDF_LIMIT = 5 * 1024 * 1024

const FIELD_IDS: Record<keyof ResumeValues, string> = {
  displayName: 'resume-name',
  headline: 'resume-headline',
  specialization: 'resume-specialization',
  city: 'resume-city',
  experienceYears: 'resume-experience',
  workFormats: 'resume-format-office',
  stack: 'resume-stack',
  softSkills: 'resume-soft',
  about: 'resume-about',
  phone: 'resume-phone',
  telegram: 'resume-telegram',
  salary: 'resume-salary',
}

type Props = {
  profile: OwnCandidateDto | null
}

export function ResumeForm({ profile }: Props) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [manual, setManual] = useState(profile !== null)
  const [values, setValues] = useState<ResumeValues>(() => resumeValuesFrom(profile))
  const [errors, setErrors] = useState<ResumeErrors>({})
  const [fileError, setFileError] = useState('')
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')
  const [saved, setSaved] = useState(false)
  const [createdHere] = useState(() => profile === null)

  const save = useMutation({
    mutationFn: candidateApi.saveResume,
    onSuccess: (next) => {
      queryClient.setQueryData(candidateKeys.mine(), next)
      setSaved(true)
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const upload = useMutation({
    mutationFn: candidateApi.uploadResume,
    onSuccess: (next) => {
      queryClient.setQueryData(candidateKeys.mine(), next)
      setValues(resumeValuesFrom(next))
      setManual(true)
      setFileError('')
      setSaved(false)
      setFormError('')
      setNotice('Проверьте распознанные поля и сохраните резюме.')
    },
    onError: (error) => {
      setManual(true)
      setFileError(
        error instanceof ApiError && error.status === 501
          ? 'Автораспознавание PDF пока недоступно. Заполните поля вручную — файл не сохранён.'
          : getErrorMessage(error),
      )
    },
  })

  const update = <K extends keyof ResumeValues>(key: K, value: ResumeValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    setSaved(false)
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const toggleFormat = (format: WorkFormat) => {
    const next = values.workFormats.includes(format)
      ? values.workFormats.filter((item) => item !== format)
      : [...values.workFormats, format]
    update('workFormats', next)
  }

  const onFile = (file: File | undefined) => {
    setFileError('')
    if (!file) return
    const isPdf = file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf')
    if (!isPdf) {
      setFileError('Нужен файл PDF. Скан без текста лучше заполнить вручную.')
      setManual(true)
      return
    }
    if (file.size > PDF_LIMIT) {
      setFileError('Файл больше 5 МБ. Сожмите его или заполните поля вручную.')
      setManual(true)
      return
    }
    upload.mutate(file)
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextErrors = validateResume(values)
    setErrors(nextErrors)
    const first = (Object.keys(FIELD_IDS) as (keyof ResumeValues)[]).find((key) => nextErrors[key])
    if (first) {
      document.getElementById(FIELD_IDS[first])?.focus()
      return
    }
    save.mutate(toResumePayload(values))
  }

  const showForm = manual || profile !== null

  return (
    <div className="resume-form">
      {!showForm && (
        <div className="resume-start">
          <p className="resume-start__lead">
            Есть готовое резюме? Приложите его, а мы попробуем вытащить из него нужные данные!
          </p>
          <div className="resume-start__actions">
            <label className="btn btn--solid btn--inline file-btn">
              {upload.isPending ? 'Читаем файл…' : 'Приложить PDF'}
              <input
                type="file"
                accept="application/pdf,.pdf"
                disabled={upload.isPending}
                onChange={(event) => onFile(event.target.files?.[0])}
              />
            </label>
            <Button variant="ghost" size="inline" onClick={() => setManual(true)}>
              Заполнить вручную
            </Button>
          </div>
          {fileError && (
            <p className="form-banner" role="alert">
              {fileError}
            </p>
          )}
        </div>
      )}

      {showForm && (
        <form className="resume-form" noValidate onSubmit={onSubmit}>
          {fileError && (
            <p className="form-banner" role="alert">
              {fileError}
            </p>
          )}
          {profile && (
            <div className="resume-start__actions">
              <label className="btn btn--ghost btn--inline file-btn">
                {upload.isPending ? 'Читаем файл…' : 'Заменить из PDF'}
                <input
                  type="file"
                  accept="application/pdf,.pdf"
                  disabled={upload.isPending}
                  onChange={(event) => onFile(event.target.files?.[0])}
                />
              </label>
            </div>
          )}

          <div className="resume-form__grid">
            <TextField
              id="resume-name"
              label="Имя и фамилия"
              autoComplete="name"
              value={values.displayName}
              error={errors.displayName}
              onChange={(event) => update('displayName', event.target.value)}
            />
            <TextField
              id="resume-headline"
              label="Должность"
              autoComplete="organization-title"
              value={values.headline}
              error={errors.headline}
              onChange={(event) => update('headline', event.target.value)}
            />
            <SelectField
              id="resume-specialization"
              label="Специализация"
              value={values.specialization}
              error={
                errors.specialization ??
                (dictionary.isError ? getErrorMessage(dictionary.error) : undefined)
              }
              disabled={dictionary.isPending}
              onChange={(event) => update('specialization', event.target.value)}
            >
              <option value="">{dictionary.isPending ? 'Загрузка…' : 'Выберите'}</option>
              {dictionary.data?.specializations.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </SelectField>
            <TextField
              id="resume-city"
              label="Город"
              autoComplete="address-level2"
              value={values.city}
              error={errors.city}
              onChange={(event) => update('city', event.target.value)}
            />
            <TextField
              id="resume-experience"
              label="Стаж, лет"
              inputMode="numeric"
              value={values.experienceYears}
              error={errors.experienceYears}
              onChange={(event) => update('experienceYears', event.target.value)}
            />
            <TextField
              id="resume-salary"
              label="Ожидаемая зарплата от, ₽"
              inputMode="numeric"
              value={values.salary}
              error={errors.salary}
              onChange={(event) => update('salary', event.target.value)}
            />
            <fieldset className="check-group resume-form__wide">
              <legend className="check-group__legend">Формат работы</legend>
              <div className="check-group__options">
                {WORK_FORMATS.map((format) => (
                  <label key={format} className="check">
                    <input
                      id={format === 'office' ? 'resume-format-office' : undefined}
                      type="checkbox"
                      checked={values.workFormats.includes(format)}
                      onChange={() => toggleFormat(format)}
                    />
                    {WORK_FORMAT_LABELS[format]}
                  </label>
                ))}
              </div>
              {errors.workFormats && (
                <p className="check-group__error" role="alert">
                  {errors.workFormats}
                </p>
              )}
            </fieldset>
            <div className="resume-form__wide">
              <TextField
                id="resume-stack"
                label="Стек"
                placeholder="Python, PostgreSQL, Docker"
                value={values.stack}
                error={errors.stack}
                onChange={(event) => update('stack', event.target.value)}
              />
              <p className="form-hint">
                От 1 до 30 навыков, через запятую. Грейд резюме не задаёт — его подтверждает тест.
              </p>
            </div>
            <div className="resume-form__wide">
              <TextField
                id="resume-soft"
                label="Софт-скиллы"
                value={values.softSkills}
                error={errors.softSkills}
                onChange={(event) => update('softSkills', event.target.value)}
              />
            </div>
            <div className="resume-form__wide">
              <TextArea
                id="resume-about"
                label="О себе"
                maxLength={2000}
                value={values.about}
                error={errors.about}
                onChange={(event) => update('about', event.target.value)}
              />
              <p className="form-hint">{values.about.trim().length} / 2000</p>
            </div>
            <TextField
              id="resume-phone"
              label="Телефон"
              type="tel"
              autoComplete="tel"
              value={values.phone}
              error={errors.phone}
              onChange={(event) => update('phone', event.target.value)}
            />
            <TextField
              id="resume-telegram"
              label="Telegram"
              autoComplete="username"
              value={values.telegram}
              error={errors.telegram}
              onChange={(event) => update('telegram', event.target.value)}
            />
          </div>

          <p className="form-hint">
            Телефон и Telegram увидит работодатель только после того, как вы примете приглашение.
          </p>

          {notice && <p className="form-status">{notice}</p>}
          {formError && (
            <p className="form-banner" role="alert">
              {formError}
            </p>
          )}
          {saved && (
            <p className="form-status" role="status">
              Резюме сохранено.
              {createdHere && (
                <>
                  {' '}
                  <Link to={ROUTES.testing}>Дальше — пройти тест</Link>
                </>
              )}
            </p>
          )}

          <div className="form-actions">
            <Button type="submit" size="inline" disabled={save.isPending}>
              {save.isPending ? 'Сохраняем…' : 'Сохранить резюме'}
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}
