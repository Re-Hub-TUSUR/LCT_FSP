import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { FSP_DISCIPLINE_LABELS } from '@/entities/candidate'
import type { FspDiscipline } from '@/entities/candidate'
import { categoryQueries, GRADE_LABELS, GRADES } from '@/entities/category'
import {
  BENEFIT_LABELS,
  BENEFITS,
  EMPLOYMENT_LABELS,
  EMPLOYMENT_TYPES,
  FSP_RESULT_LABELS,
  SALARY_NOTE,
  vacancyApi,
  vacancyKeys,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import type { FspResult, VacancyDto } from '@/entities/vacancy'
import { getErrorMessage } from '@/shared/api'
import { STACK_SKILLS } from '@/shared/config'
import { toggled } from '@/shared/lib'
import {
  Button,
  CheckRow,
  Segmented,
  SelectField,
  SkillField,
  TextArea,
  TextField,
} from '@/shared/ui'
import {
  DESCRIPTION_MAX,
  DESCRIPTION_MIN,
  EXPERIENCE_OPTIONS,
  TITLE_MAX,
  toggleGrade,
  toVacancyPayload,
  vacancyValuesFrom,
  validateVacancy,
} from '../model/schema'
import type { VacancyErrorKey, VacancyErrors, VacancyValues } from '../model/schema'
import './vacancy-form.css'

/** In the order of the form: the first field with an error gets the focus. */
const FIELD_IDS: Record<VacancyErrorKey, string> = {
  title: 'vacancy-title',
  specialization: 'vacancy-specialization',
  grades: 'vacancy-grade-intern',
  description: 'vacancy-description',
  stackRequired: 'vacancy-stack-required',
  salaryFrom: 'vacancy-salary-from',
  salaryTo: 'vacancy-salary-to',
  city: 'vacancy-city',
  employmentTypes: 'vacancy-employment',
}

const FORMAT_ITEMS = WORK_FORMATS.map((format) => ({
  value: format,
  label: WORK_FORMAT_LABELS[format],
}))

type Props = {
  /** Null: a new vacancy. */
  vacancy: VacancyDto | null
  onSaved: (vacancy: VacancyDto) => void
}

/** The recruiter's vacancy form: published at once or kept as a draft only the company sees. */
export function VacancyForm({ vacancy, onSaved }: Props) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [values, setValues] = useState<VacancyValues>(() => vacancyValuesFrom(vacancy))
  const [errors, setErrors] = useState<VacancyErrors>({})
  const [formError, setFormError] = useState('')
  const published = Boolean(vacancy?.publishedAt)
  const remote = values.workFormat === 'remote'

  const save = useMutation({
    mutationFn: (publish: boolean) => {
      const payload = toVacancyPayload(values, publish)
      return vacancy ? vacancyApi.update(vacancy.id, payload) : vacancyApi.create(payload)
    },
    onSuccess: async (saved) => {
      await queryClient.invalidateQueries({ queryKey: vacancyKeys.all })
      onSaved(saved)
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const update = <K extends keyof VacancyValues>(key: K, value: VacancyValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (key in FIELD_IDS && errors[key as VacancyErrorKey]) {
      setErrors((prev) => ({ ...prev, [key]: undefined }))
    }
  }

  const submit = (publish: boolean) => {
    const nextErrors = validateVacancy(values)
    setErrors(nextErrors)
    setFormError('')
    const first = (Object.keys(FIELD_IDS) as VacancyErrorKey[]).find((key) => nextErrors[key])
    if (first) {
      document.getElementById(FIELD_IDS[first])?.focus()
      return
    }
    save.mutate(publish)
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submit(true)
  }

  const length = values.description.trim().length

  return (
    <form className="vacancy-form" noValidate onSubmit={onSubmit}>
      <fieldset className="vacancy-form__group">
        <legend className="vacancy-form__legend">О вакансии</legend>
        <div className="vacancy-form__grid">
          <div className="vacancy-form__wide">
            <TextField
              id="vacancy-title"
              label="Название"
              maxLength={TITLE_MAX}
              placeholder="Backend-разработчик (платежи)"
              value={values.title}
              error={errors.title}
              onChange={(event) => update('title', event.target.value)}
            />
          </div>
          <SelectField
            id="vacancy-specialization"
            label="Специализация"
            value={values.specialization}
            error={errors.specialization}
            onChange={(event) => update('specialization', event.target.value)}
          >
            <option value="">Не выбрана</option>
            {dictionary.data?.specializations.map((item) => (
              <option key={item.code} value={item.code}>
                {item.label}
              </option>
            ))}
          </SelectField>
          <div className="vacancy-form__field">
            <p className="field__label" id="vacancy-grades-label">
              Грейд
            </p>
            <div
              className="vacancy-form__chips"
              role="group"
              aria-labelledby="vacancy-grades-label"
            >
              {GRADES.map((grade) => (
                <button
                  key={grade}
                  id={`vacancy-grade-${grade}`}
                  type="button"
                  className={
                    values.grades.includes(grade)
                      ? 'vacancy-form__chip is-on'
                      : 'vacancy-form__chip'
                  }
                  aria-pressed={values.grades.includes(grade)}
                  onClick={() => update('grades', toggleGrade(values.grades, grade))}
                >
                  {GRADE_LABELS[grade]}
                </button>
              ))}
            </div>
            <p className="vacancy-form__hint">Один грейд или два соседних.</p>
            <p className="field__error" role="alert">
              {errors.grades}
            </p>
          </div>
          <div className="vacancy-form__wide">
            <TextArea
              id="vacancy-description"
              label="Описание"
              rows={12}
              maxLength={DESCRIPTION_MAX}
              placeholder={
                'Чем занимается команда.\n\nЗадачи:\n— …\n\nТребования:\n— …\n\nУсловия:\n— …'
              }
              value={values.description}
              error={errors.description}
              onChange={(event) => update('description', event.target.value)}
            />
            <p className="vacancy-form__hint">
              {length} / {DESCRIPTION_MAX}
              {length < DESCRIPTION_MIN ? ` · минимум ${DESCRIPTION_MIN}` : ''} · абзацы разделяйте
              пустой строкой
            </p>
          </div>
        </div>
      </fieldset>

      <fieldset className="vacancy-form__group">
        <legend className="vacancy-form__legend">Стек</legend>
        <div className="vacancy-form__grid">
          <SkillField
            id="vacancy-stack-required"
            label="Обязательно"
            catalog={STACK_SKILLS}
            value={values.stackRequired}
            error={errors.stackRequired}
            onChange={(next) => update('stackRequired', next)}
          />
          <SkillField
            id="vacancy-stack-nice"
            label="Будет плюсом"
            catalog={STACK_SKILLS}
            value={values.stackNice}
            onChange={(next) => update('stackNice', next)}
          />
        </div>
      </fieldset>

      <fieldset className="vacancy-form__group">
        <legend className="vacancy-form__legend">Условия</legend>
        <div className="vacancy-form__grid">
          <div>
            <TextField
              id="vacancy-salary-from"
              label="Зарплата от, ₽"
              inputMode="numeric"
              placeholder="200 000"
              value={values.salaryFrom}
              error={errors.salaryFrom}
              onChange={(event) => update('salaryFrom', event.target.value)}
            />
          </div>
          <div>
            <TextField
              id="vacancy-salary-to"
              label="Зарплата до, ₽"
              inputMode="numeric"
              placeholder="320 000"
              value={values.salaryTo}
              error={errors.salaryTo}
              onChange={(event) => update('salaryTo', event.target.value)}
            />
            <p className="vacancy-form__hint">Вилка обязательна; суммы — {SALARY_NOTE}.</p>
          </div>
          <div className="vacancy-form__field">
            <p className="field__label">Формат работы</p>
            <Segmented
              label="Формат работы"
              items={FORMAT_ITEMS}
              value={values.workFormat}
              onChange={(value) => update('workFormat', value)}
            />
          </div>
          {!remote && (
            <div>
              <TextField
                id="vacancy-city"
                label="Город офиса"
                autoComplete="address-level2"
                value={values.city}
                error={errors.city}
                onChange={(event) => update('city', event.target.value)}
              />
              <div className="vacancy-form__under">
                <CheckRow
                  checked={values.relocationHelp}
                  onChange={(checked) => update('relocationHelp', checked)}
                >
                  Помогаем с переездом
                </CheckRow>
              </div>
            </div>
          )}
          <div className="vacancy-form__field">
            <p className="field__label" id="vacancy-employment-label">
              Тип занятости
            </p>
            <div
              id="vacancy-employment"
              className="vacancy-form__checks"
              role="group"
              aria-labelledby="vacancy-employment-label"
              tabIndex={-1}
            >
              {EMPLOYMENT_TYPES.map((type) => (
                <CheckRow
                  key={type}
                  checked={values.employmentTypes.includes(type)}
                  onChange={() => update('employmentTypes', toggled(values.employmentTypes, type))}
                >
                  {EMPLOYMENT_LABELS[type]}
                </CheckRow>
              ))}
            </div>
            <p className="field__error" role="alert">
              {errors.employmentTypes}
            </p>
          </div>
          <div className="vacancy-form__field">
            <p className="field__label" id="vacancy-benefits-label">
              Что предлагаете
            </p>
            <div
              className="vacancy-form__checks"
              role="group"
              aria-labelledby="vacancy-benefits-label"
            >
              {BENEFITS.map((benefit) => (
                <CheckRow
                  key={benefit}
                  checked={values.benefits.includes(benefit)}
                  onChange={() => update('benefits', toggled(values.benefits, benefit))}
                >
                  {BENEFIT_LABELS[benefit]}
                </CheckRow>
              ))}
            </div>
          </div>
        </div>
      </fieldset>

      <fieldset className="vacancy-form__group">
        <legend className="vacancy-form__legend">Требования к кандидату</legend>
        <div className="vacancy-form__grid">
          <SelectField
            id="vacancy-experience"
            label="Коммерческий опыт"
            value={values.minExperienceYears}
            onChange={(event) => update('minExperienceYears', Number(event.target.value))}
          >
            {EXPERIENCE_OPTIONS.map((item) => (
              <option key={item.value} value={item.value}>
                {item.label}
              </option>
            ))}
          </SelectField>
          <div className="vacancy-form__field vacancy-form__field--center">
            <CheckRow
              checked={values.verifiedGradeOnly}
              onChange={(checked) => update('verifiedGradeOnly', checked)}
            >
              Только с грейдом, подтверждённым тестом
            </CheckRow>
          </div>
          <SelectField
            id="vacancy-fsp-result"
            label="Результат ФСП не ниже"
            value={values.fspBestResult}
            onChange={(event) => update('fspBestResult', event.target.value as FspResult | '')}
          >
            <option value="">Не важен</option>
            {(Object.keys(FSP_RESULT_LABELS) as FspResult[]).map((result) => (
              <option key={result} value={result}>
                {FSP_RESULT_LABELS[result]}
              </option>
            ))}
          </SelectField>
          <SelectField
            id="vacancy-fsp-discipline"
            label="Дисциплина ФСП"
            value={values.fspBestResult ? values.fspDiscipline : ''}
            disabled={!values.fspBestResult}
            onChange={(event) => update('fspDiscipline', event.target.value as FspDiscipline | '')}
          >
            <option value="">Любая</option>
            {(Object.keys(FSP_DISCIPLINE_LABELS) as FspDiscipline[]).map((discipline) => (
              <option key={discipline} value={discipline}>
                {FSP_DISCIPLINE_LABELS[discipline]}
              </option>
            ))}
          </SelectField>
        </div>
        <p className="vacancy-form__hint">
          С этими требованиями откроется подбор кандидатов под вакансию; в подборе их можно
          ослабить.
        </p>
      </fieldset>

      {formError && (
        <p className="vacancy-form__banner" role="alert">
          {formError}
        </p>
      )}

      <div className="vacancy-form__actions">
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : published ? 'Сохранить' : 'Опубликовать'}
        </Button>
        <Button
          type="button"
          variant="ghost"
          size="inline"
          disabled={save.isPending}
          onClick={() => submit(false)}
        >
          {published ? 'Снять с публикации' : 'Сохранить черновик'}
        </Button>
      </div>
    </form>
  )
}
