import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { candidateApi, candidateKeys } from '@/entities/candidate'
import type { OwnCandidateDto, ResumeDto } from '@/entities/candidate'
import { categoryQueries } from '@/entities/category'
import { getErrorMessage } from '@/shared/api'
import { STACK_SKILLS } from '@/shared/config'
import { Button, SelectField, SkillField, TextArea, TextField } from '@/shared/ui'
import { EMPTY_RESUME, toExtraResume, validateExtra } from '../model/schema'
import type { ResumeErrors, ResumeValues } from '../model/schema'
import { SOFT_SKILLS } from '../model/skills'

export const MAX_RESUMES = 3

const EXTRA_IDS: Partial<Record<keyof ResumeValues, string>> = {
  headline: 'extra-headline',
  specialization: 'extra-specialization',
  experienceYears: 'extra-experience',
  stack: 'extra-stack',
  softSkills: 'extra-soft',
  about: 'extra-about',
}

/** The primary resume and up to two more: list, «make primary» and the form for another one. */
export function ExtraResumes({ profile }: { profile: OwnCandidateDto }) {
  const queryClient = useQueryClient()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [open, setOpen] = useState(false)
  const [values, setValues] = useState<ResumeValues>(EMPTY_RESUME)
  const [errors, setErrors] = useState<ResumeErrors>({})
  const [formError, setFormError] = useState('')

  const remember = (next: OwnCandidateDto) => queryClient.setQueryData(candidateKeys.mine(), next)

  const addResume = useMutation({
    mutationFn: candidateApi.addResume,
    onSuccess: (next) => {
      remember(next)
      setOpen(false)
      setValues(EMPTY_RESUME)
      setErrors({})
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const makePrimary = useMutation({
    mutationFn: candidateApi.makePrimary,
    onSuccess: (next) => {
      remember(next)
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const resumes = profile.resumes ?? []
  const canAdd = resumes.length < MAX_RESUMES
  const labelOf = (code: string | null) =>
    dictionary.data?.specializations.find((item) => item.code === code)?.label ?? code ?? 'Профиль'

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const next = validateExtra(values)
    setErrors(next)
    const first = (Object.keys(EXTRA_IDS) as (keyof ResumeValues)[]).find((key) => next[key])
    if (first) {
      document.getElementById(EXTRA_IDS[first] ?? '')?.focus()
      return
    }
    addResume.mutate(toExtraResume(values))
  }

  return (
    <div className="resume-form">
      {resumes.length > 0 && (
        <ul className="resume-list" aria-label="Ваши резюме">
          {resumes.map((resume) => (
            <ResumeRow
              key={resume.id}
              resume={resume}
              title={`${labelOf(resume.specialization)}${resume.headline ? ` · ${resume.headline}` : ''}`}
              busy={makePrimary.isPending}
              onPrimary={() => makePrimary.mutate(resume.id)}
            />
          ))}
        </ul>
      )}
      <p className="form-hint">
        Например, Backend и DevOps. Приоритетное резюме работодатель видит первым, остальные — как
        дополнительные профили. Всего до {MAX_RESUMES}.
      </p>
      {formError && (
        <p className="form-banner" role="alert">
          {formError}
        </p>
      )}
      {canAdd && !open && (
        <div className="form-actions">
          <Button type="button" variant="ghost" size="inline" onClick={() => setOpen(true)}>
            Ещё одно резюме
          </Button>
        </div>
      )}
      {open && (
        <form className="resume-form resume-extra" noValidate onSubmit={onSubmit}>
          <div className="resume-form__grid">
            <TextField
              id="extra-headline"
              label="Должность"
              value={values.headline}
              error={errors.headline}
              onChange={(event) => setValues((prev) => ({ ...prev, headline: event.target.value }))}
            />
            <SelectField
              id="extra-specialization"
              label="Специализация"
              value={values.specialization}
              error={errors.specialization}
              disabled={dictionary.isPending}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, specialization: event.target.value }))
              }
            >
              <option value="">{dictionary.isPending ? 'Загрузка…' : 'Выберите'}</option>
              {dictionary.data?.specializations.map((item) => (
                <option key={item.code} value={item.code}>
                  {item.label}
                </option>
              ))}
            </SelectField>
            <TextField
              id="extra-experience"
              label="Стаж, лет"
              inputMode="numeric"
              value={values.experienceYears}
              error={errors.experienceYears}
              onChange={(event) =>
                setValues((prev) => ({ ...prev, experienceYears: event.target.value }))
              }
            />
            <div className="resume-form__wide">
              <SkillField
                id="extra-stack"
                label="Стек"
                catalog={STACK_SKILLS}
                value={values.stack}
                error={errors.stack}
                onChange={(next) => setValues((prev) => ({ ...prev, stack: next }))}
              />
            </div>
            <div className="resume-form__wide">
              <SkillField
                id="extra-soft"
                label="Софт-скиллы"
                catalog={SOFT_SKILLS}
                value={values.softSkills}
                error={errors.softSkills}
                onChange={(next) => setValues((prev) => ({ ...prev, softSkills: next }))}
              />
            </div>
            <div className="resume-form__wide">
              <TextArea
                id="extra-about"
                label="О себе"
                maxLength={2000}
                value={values.about}
                error={errors.about}
                onChange={(event) => setValues((prev) => ({ ...prev, about: event.target.value }))}
              />
            </div>
          </div>
          <div className="form-actions">
            <Button type="submit" size="inline" disabled={addResume.isPending}>
              {addResume.isPending ? 'Сохраняем…' : 'Сохранить ещё одно'}
            </Button>
            <Button type="button" variant="ghost" size="inline" onClick={() => setOpen(false)}>
              Отмена
            </Button>
          </div>
        </form>
      )}
    </div>
  )
}

function ResumeRow({
  resume,
  title,
  busy,
  onPrimary,
}: {
  resume: ResumeDto
  title: string
  busy: boolean
  onPrimary: () => void
}) {
  return (
    <li className="resume-list__item">
      <span
        className={
          resume.isPrimary ? 'resume-list__badge' : 'resume-list__badge resume-list__badge--muted'
        }
      >
        {resume.isPrimary ? 'Приоритетное' : 'Второстепенное'}
      </span>
      <span className="resume-list__title">{title}</span>
      {!resume.isPrimary && (
        <Button type="button" variant="ghost" size="inline" disabled={busy} onClick={onPrimary}>
          Сделать приоритетным
        </Button>
      )}
    </li>
  )
}
