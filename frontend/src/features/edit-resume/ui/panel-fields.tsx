import { useQuery } from '@tanstack/react-query'
import { JOB_STATUS_LABELS, JOB_STATUSES } from '@/entities/candidate'
import type { JobStatus } from '@/entities/candidate'
import { categoryQueries } from '@/entities/category'
import {
  EMPLOYMENT_LABELS,
  EMPLOYMENT_TYPES,
  SALARY_NOTE,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import { getErrorMessage } from '@/shared/api'
import { STACK_SKILLS } from '@/shared/config'
import { SelectField, SkillField, TextArea, TextField } from '@/shared/ui'
import type { PanelId } from '../model/panels'
import type { ResumeErrors, ResumeValues } from '../model/schema'
import { SOFT_SKILLS } from '../model/skills'
import { EducationField } from './education-field'
import { ExperienceField } from './experience-field'

type Props = {
  panel: PanelId
  values: ResumeValues
  errors: ResumeErrors
  update: <K extends keyof ResumeValues>(key: K, value: ResumeValues[K]) => void
}

function toggle<T>(items: T[], item: T): T[] {
  return items.includes(item) ? items.filter((value) => value !== item) : [...items, item]
}

/** Inputs of one panel; ids match RESUME_FIELD_IDS so the first error gets the focus. */
export function PanelFields({ panel, values, errors, update }: Props) {
  const dictionary = useQuery({ ...categoryQueries.dictionary(), enabled: panel === 'basic' })

  if (panel === 'basic') {
    return (
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
        <div>
          <TextField
            id="resume-birth"
            label="Дата рождения"
            type="date"
            autoComplete="bday"
            value={values.birthDate}
            error={errors.birthDate}
            onChange={(event) => update('birthDate', event.target.value)}
          />
          <p className="form-hint resume-form__note">
            Не показываем работодателю. Если вам нет 18, он увидит только пометку
            «несовершеннолетний».
          </p>
        </div>
      </div>
    )
  }

  if (panel === 'search') {
    return (
      <div className="resume-form__grid">
        <SelectField
          id="resume-status"
          label="Статус поиска"
          value={values.jobStatus}
          onChange={(event) => update('jobStatus', event.target.value as JobStatus)}
        >
          {JOB_STATUSES.map((status) => (
            <option key={status} value={status}>
              {JOB_STATUS_LABELS[status]}
            </option>
          ))}
        </SelectField>
        <div>
          <TextField
            id="resume-salary"
            label="Ожидаемая зарплата от, ₽"
            inputMode="numeric"
            value={values.salary}
            error={errors.salary}
            onChange={(event) => update('salary', event.target.value)}
          />
          <p className="form-hint resume-form__note">{SALARY_NOTE}</p>
        </div>
        <fieldset className="check-group resume-form__relocation">
          <legend className="check-group__legend">Переезд</legend>
          <label className="check">
            <input
              id="resume-relocation"
              type="checkbox"
              checked={values.relocationReady}
              onChange={(event) => update('relocationReady', event.target.checked)}
            />
            Готов к переезду
          </label>
        </fieldset>
        <fieldset className="check-group resume-form__wide">
          <legend className="check-group__legend">Формат работы</legend>
          <div className="check-group__options">
            {WORK_FORMATS.map((format) => (
              <label key={format} className="check">
                <input
                  id={format === 'office' ? 'resume-format-office' : undefined}
                  type="checkbox"
                  checked={values.workFormats.includes(format)}
                  onChange={() => update('workFormats', toggle(values.workFormats, format))}
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
        <fieldset className="check-group resume-form__wide">
          <legend className="check-group__legend">Тип занятости</legend>
          <div className="check-group__options">
            {EMPLOYMENT_TYPES.map((type) => (
              <label key={type} className="check">
                <input
                  id={`resume-employment-${type}`}
                  type="checkbox"
                  checked={values.employmentTypes.includes(type)}
                  onChange={() => update('employmentTypes', toggle(values.employmentTypes, type))}
                />
                {EMPLOYMENT_LABELS[type]}
              </label>
            ))}
          </div>
          {errors.employmentTypes && (
            <p className="check-group__error" role="alert">
              {errors.employmentTypes}
            </p>
          )}
        </fieldset>
      </div>
    )
  }

  if (panel === 'experience') {
    return (
      <div className="resume-form__grid">
        <ExperienceField
          rows={values.experience}
          noExperience={values.noExperience}
          years={values.experienceYears}
          error={errors.experience}
          yearsError={errors.experienceYears}
          onRows={(rows) => update('experience', rows)}
          onNoExperience={(value) => update('noExperience', value)}
          onYears={(value) => update('experienceYears', value)}
        />
      </div>
    )
  }

  if (panel === 'skills') {
    return (
      <div className="resume-form__grid">
        <div className="resume-form__wide">
          <SkillField
            id="resume-stack"
            label="Стек"
            catalog={STACK_SKILLS}
            value={values.stack}
            error={errors.stack}
            onChange={(next) => update('stack', next)}
          />
          <p className="form-hint">
            Не меньше трёх технологий. Грейд резюме не задаёт — его подтверждает тест.
          </p>
        </div>
        <div className="resume-form__wide">
          <SkillField
            id="resume-soft"
            label="Софт-скиллы"
            catalog={SOFT_SKILLS}
            value={values.softSkills}
            error={errors.softSkills}
            onChange={(next) => update('softSkills', next)}
          />
        </div>
      </div>
    )
  }

  if (panel === 'education') {
    return (
      <div className="resume-form__grid">
        <EducationField
          rows={values.education}
          error={errors.education}
          onRows={(rows) => update('education', rows)}
        />
      </div>
    )
  }

  if (panel === 'about') {
    return (
      <div>
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
    )
  }

  return (
    <div className="resume-form__grid">
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
      <TextField
        id="resume-github"
        label="GitHub (необязательно)"
        type="url"
        placeholder="github.com/login"
        value={values.githubUrl}
        error={errors.githubUrl}
        onChange={(event) => update('githubUrl', event.target.value)}
      />
    </div>
  )
}
