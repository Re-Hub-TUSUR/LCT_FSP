import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { Link } from 'react-router'
import {
  candidateApi,
  candidateKeys,
  dropPhotoUrl,
  JOB_STATUS_LABELS,
  JOB_STATUSES,
} from '@/entities/candidate'
import type { JobStatus, OwnCandidateDto, ResumeDto } from '@/entities/candidate'
import { categoryQueries } from '@/entities/category'
import { useSession } from '@/entities/session'
import {
  EMPLOYMENT_LABELS,
  EMPLOYMENT_TYPES,
  SALARY_NOTE,
  WORK_FORMAT_LABELS,
  WORK_FORMATS,
} from '@/entities/vacancy'
import type { EmploymentType, WorkFormat } from '@/entities/vacancy'
import { getErrorMessage, http } from '@/shared/api'
import { ROUTES, STACK_SKILLS } from '@/shared/config'
import { Button, CitySelect, SelectField, SkillField, TextArea, TextField } from '@/shared/ui'
import { draftPhotoFile, photoFileError, resumeFileError, resumeUploadError } from '../model/files'
import {
  applyResumeDraft,
  EMPTY_RESUME,
  RESUME_FIELD_IDS,
  resumeValuesFrom,
  toExtraResume,
  toResumePayload,
  validateExtra,
  validateResume,
} from '../model/schema'
import type { ResumeErrors, ResumeValues } from '../model/schema'
import { SOFT_SKILLS } from '../model/skills'
import { EducationField } from './education-field'
import { ExperienceField } from './experience-field'
import { PhotoField } from './photo-field'
import { consentsGiven, EMPTY_CONSENTS, ResumeConsents } from './resume-consents'
import type { ConsentValues } from './resume-consents'
import { rememberFirstResume } from './resume-next-step'
import './resume-form.css'

const MAX_RESUMES = 3

const FIELD_IDS = RESUME_FIELD_IDS

function toggle<T>(items: T[], item: T): T[] {
  return items.includes(item) ? items.filter((value) => value !== item) : [...items, item]
}

const EXTRA_IDS: Partial<Record<keyof ResumeValues, string>> = {
  headline: 'extra-headline',
  specialization: 'extra-specialization',
  experienceYears: 'extra-experience',
  stack: 'extra-stack',
  softSkills: 'extra-soft',
  about: 'extra-about',
}

type Props = {
  profile: OwnCandidateDto | null
}

export function ResumeForm({ profile }: Props) {
  const queryClient = useQueryClient()
  const { user } = useSession()
  const dictionary = useQuery(categoryQueries.dictionary())
  const hintedName = [user?.firstName, user?.lastName].filter(Boolean).join(' ')
  const [manual, setManual] = useState(profile !== null)
  const [values, setValues] = useState<ResumeValues>(() =>
    resumeValuesFrom(profile, profile ? '' : hintedName),
  )
  const [errors, setErrors] = useState<ResumeErrors>({})
  const [fileError, setFileError] = useState('')
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')
  const [saved, setSaved] = useState(false)
  const [createdHere] = useState(() => profile === null)
  const [askAnother, setAskAnother] = useState(false)
  const [extraOpen, setExtraOpen] = useState(false)
  const [extraValues, setExtraValues] = useState<ResumeValues>(EMPTY_RESUME)
  const [extraErrors, setExtraErrors] = useState<ResumeErrors>({})
  const [pendingPhoto, setPendingPhoto] = useState<File | null>(null)
  const [previewUrl, setPreviewUrl] = useState<string | null>(null)
  const [yandexPreview, setYandexPreview] = useState<string | null>(null)
  const [photoError, setPhotoError] = useState('')
  const [consents, setConsents] = useState<ConsentValues>(EMPTY_CONSENTS)

  useEffect(() => {
    if (profile) return
    let alive = true
    let objectUrl = ''
    void http
      .blob('/users/me/pending-photo')
      .then((blob) => {
        if (!alive) return
        objectUrl = URL.createObjectURL(blob)
        setYandexPreview(objectUrl)
      })
      .catch(() => {})
    return () => {
      alive = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [profile])

  const remember = (next: OwnCandidateDto) => {
    queryClient.setQueryData(candidateKeys.mine(), next)
  }

  const save = useMutation({
    mutationFn: candidateApi.saveResume,
    onSuccess: (next) => {
      remember(next)
      setSaved(true)
      setFormError('')
      // A file that could not be read no longer matters once the resume is saved by hand.
      setFileError('')
      setAskAnother(true)
      if (createdHere) rememberFirstResume(consents.fspSync === 'yes' && !next.fspMemberId)
      if (pendingPhoto) uploadPhoto.mutate(pendingPhoto)
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  // The server only recognises the fields: nothing is stored until the candidate saves the form.
  const upload = useMutation({
    mutationFn: candidateApi.uploadResume,
    onSuccess: (draft) => {
      setValues((prev) => applyResumeDraft(prev, draft))
      // The portrait from the file is uploaded with the save, unless a photo is already chosen.
      const photo =
        draft.photo && !pendingPhoto && !profile?.hasPhoto ? draftPhotoFile(draft.photo) : null
      if (photo) {
        setPreviewUrl((current) => {
          if (current) URL.revokeObjectURL(current)
          return URL.createObjectURL(photo)
        })
        setPendingPhoto(photo)
      }
      setErrors({})
      setManual(true)
      setFileError('')
      setSaved(false)
      setFormError('')
      setNotice('Проверьте распознанные поля и сохраните резюме.')
    },
    onError: (error) => {
      setManual(true)
      setFileError(resumeUploadError(error))
    },
  })

  const addResume = useMutation({
    mutationFn: candidateApi.addResume,
    onSuccess: (next) => {
      remember(next)
      setExtraOpen(false)
      setExtraValues(EMPTY_RESUME)
      setExtraErrors({})
      setAskAnother((next.resumes?.length ?? 1) < MAX_RESUMES)
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const makePrimary = useMutation({
    mutationFn: candidateApi.makePrimary,
    onSuccess: (next) => {
      remember(next)
      setValues(resumeValuesFrom(next))
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const uploadPhoto = useMutation({
    mutationFn: candidateApi.uploadPhoto,
    onSuccess: (next) => {
      remember(next)
      dropPhotoUrl(next.id)
      setPendingPhoto(null)
      setPhotoError('')
      void queryClient.invalidateQueries({ queryKey: [...candidateKeys.all, 'photo', next.id] })
    },
    onError: (error) => setPhotoError(getErrorMessage(error)),
  })

  const update = <K extends keyof ResumeValues>(key: K, value: ResumeValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    setSaved(false)
    setAskAnother(false)
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const toggleFormat = (format: WorkFormat) =>
    update('workFormats', toggle(values.workFormats, format))
  const toggleEmployment = (type: EmploymentType) =>
    update('employmentTypes', toggle(values.employmentTypes, type))

  const onFile = async (file: File | undefined) => {
    setFileError('')
    if (!file) return
    const message = await resumeFileError(file)
    if (message) {
      setFileError(message)
      return
    }
    upload.mutate(file)
  }

  const onPhoto = async (file: File) => {
    const message = await photoFileError(file)
    if (message) {
      setPhotoError(message)
      return
    }
    setPhotoError('')
    setPreviewUrl((current) => {
      if (current) URL.revokeObjectURL(current)
      return URL.createObjectURL(file)
    })
    setPendingPhoto(file)
    if (profile) uploadPhoto.mutate(file)
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
    save.mutate(
      toResumePayload(
        values,
        profile
          ? undefined
          : // The display consent is part of the consent given at registration.
            { profileDisplayConsent: true, fspSync: consents.fspSync },
      ),
    )
  }

  const onExtra = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextErrors = validateExtra(extraValues)
    setExtraErrors(nextErrors)
    const first = (Object.keys(EXTRA_IDS) as (keyof ResumeValues)[]).find((key) => nextErrors[key])
    if (first) {
      document.getElementById(EXTRA_IDS[first] ?? '')?.focus()
      return
    }
    addResume.mutate(toExtraResume(extraValues))
  }

  const showForm = manual || profile !== null
  /**
   * The short start block turns into the long form. The browser keeps whatever was on screen in
   * place (scroll anchoring) and the page jumps; the form, its notice and its errors start at the
   * top instead, before the first paint of the form.
   */
  const formShown = useRef(showForm)
  useLayoutEffect(() => {
    if (showForm && !formShown.current) window.scrollTo({ top: 0 })
    formShown.current = showForm
  }, [showForm])
  const resumes = profile?.resumes ?? []
  const canAdd = resumes.length < MAX_RESUMES
  const labelOf = (code: string | null) =>
    dictionary.data?.specializations.find((item) => item.code === code)?.label ?? code ?? 'Профиль'

  return (
    <div className="resume-form">
      {!showForm && (
        <div className="resume-start">
          <ResumeConsents values={consents} onChange={setConsents} />
          <p className="resume-start__lead">
            Есть готовое резюме? Приложите его, а мы попробуем вытащить из него нужные данные!
          </p>
          <div className="resume-start__actions">
            <label
              className={`btn btn--solid btn--inline file-btn${consentsGiven(consents) ? '' : ' is-disabled'}`}
            >
              {upload.isPending ? 'Читаем файл…' : 'Приложить резюме'}
              <input
                type="file"
                accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                disabled={upload.isPending || !consentsGiven(consents)}
                onChange={(event) => {
                  void onFile(event.target.files?.[0])
                  event.target.value = ''
                }}
              />
            </label>
            <Button
              variant="ghost"
              size="inline"
              disabled={!consentsGiven(consents)}
              onClick={() => setManual(true)}
            >
              Заполнить вручную
            </Button>
          </div>
          {!consentsGiven(consents) && (
            <p className="form-hint">Ответьте про ФСП, чтобы продолжить.</p>
          )}
          <p className="form-hint">
            PDF или DOCX, не больше 5 МБ. Файл не сохраняется: текст без контактов читает нейросеть,
            а вы проверяете поля перед сохранением.
          </p>
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
                {upload.isPending ? 'Читаем файл…' : 'Приложить резюме'}
                <input
                  type="file"
                  accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
                  disabled={upload.isPending}
                  onChange={(event) => {
                    void onFile(event.target.files?.[0])
                    event.target.value = ''
                  }}
                />
              </label>
            </div>
          )}

          <PhotoField
            candidateId={profile?.id ?? null}
            hasPhoto={profile?.hasPhoto === true}
            previewUrl={previewUrl ?? yandexPreview}
            error={photoError}
            busy={uploadPhoto.isPending}
            onPick={(file) => void onPhoto(file)}
          />

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
            <CitySelect
              id="resume-city"
              label="Город"
              name={values.city}
              error={errors.city}
              hint={values.cityHint}
              onPick={(city) => {
                update('cityId', city.id)
                update('city', city.name)
                update('cityHint', '')
              }}
              onClear={() => {
                update('cityId', null)
                update('city', '')
              }}
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
            <fieldset className="check-group resume-form__wide">
              <legend className="check-group__legend">Тип занятости</legend>
              <div className="check-group__options">
                {EMPLOYMENT_TYPES.map((type) => (
                  <label key={type} className="check">
                    <input
                      id={`resume-employment-${type}`}
                      type="checkbox"
                      checked={values.employmentTypes.includes(type)}
                      onChange={() => toggleEmployment(type)}
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
                Не меньше трёх технологий. Начните вводить название или выберите готовый навык.
                Грейд резюме не задаёт — его подтверждает тест.
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
            <EducationField
              rows={values.education}
              error={errors.education}
              onRows={(rows) => update('education', rows)}
            />
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

          <p className="form-hint">
            Нужен телефон или Telegram. Работодатель увидит их только после того, как вы примете
            приглашение или откликнетесь.
          </p>

          {notice && <p className="form-status">{notice}</p>}
          {formError && (
            <p className="form-banner" role="alert">
              {formError}
            </p>
          )}
          {saved && (
            <p className="form-status" role="status">
              Резюме сохранено. Оно приоритетное: вакансии подбираются по нему в первую очередь.
              {createdHere && !askAnother && !extraOpen && (
                <>
                  {' '}
                  <Link to={ROUTES.testing}>Дальше — пройти тест</Link>
                </>
              )}
            </p>
          )}

          {profile && canAdd && !extraOpen && !askAnother && (
            <div className="form-actions">
              <Button
                type="button"
                variant="ghost"
                size="inline"
                onClick={() => setExtraOpen(true)}
              >
                Ещё одно резюме
              </Button>
            </div>
          )}

          {askAnother && canAdd && !extraOpen && (
            <div className="resume-ask">
              <p className="resume-start__lead">Желаете ли вы создать ещё одно резюме?</p>
              <p className="form-hint">
                Например, Backend и DevOps. Приоритетное резюме работодатель видит первым, остальные
                — как дополнительные профили.
              </p>
              <div className="resume-start__actions">
                <Button
                  type="button"
                  size="inline"
                  onClick={() => {
                    setAskAnother(false)
                    setExtraOpen(true)
                  }}
                >
                  Да, ещё одно
                </Button>
                <Button
                  type="button"
                  variant="ghost"
                  size="inline"
                  onClick={() => setAskAnother(false)}
                >
                  Нет, достаточно
                </Button>
              </div>
            </div>
          )}

          <div className="form-actions">
            <Button type="submit" size="inline" disabled={save.isPending}>
              {save.isPending ? 'Сохраняем…' : 'Сохранить резюме'}
            </Button>
          </div>
        </form>
      )}

      {extraOpen && (
        <form className="resume-form resume-extra" noValidate onSubmit={onExtra}>
          <p className="resume-start__lead">Ещё один профиль</p>
          <div className="resume-form__grid">
            <TextField
              id="extra-headline"
              label="Должность"
              value={extraValues.headline}
              error={extraErrors.headline}
              onChange={(event) =>
                setExtraValues((prev) => ({ ...prev, headline: event.target.value }))
              }
            />
            <SelectField
              id="extra-specialization"
              label="Специализация"
              value={extraValues.specialization}
              error={extraErrors.specialization}
              disabled={dictionary.isPending}
              onChange={(event) =>
                setExtraValues((prev) => ({ ...prev, specialization: event.target.value }))
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
              value={extraValues.experienceYears}
              error={extraErrors.experienceYears}
              onChange={(event) =>
                setExtraValues((prev) => ({ ...prev, experienceYears: event.target.value }))
              }
            />
            <div className="resume-form__wide">
              <SkillField
                id="extra-stack"
                label="Стек"
                catalog={STACK_SKILLS}
                value={extraValues.stack}
                error={extraErrors.stack}
                onChange={(next) => setExtraValues((prev) => ({ ...prev, stack: next }))}
              />
            </div>
            <div className="resume-form__wide">
              <SkillField
                id="extra-soft"
                label="Софт-скиллы"
                catalog={SOFT_SKILLS}
                value={extraValues.softSkills}
                error={extraErrors.softSkills}
                onChange={(next) => setExtraValues((prev) => ({ ...prev, softSkills: next }))}
              />
            </div>
            <div className="resume-form__wide">
              <TextArea
                id="extra-about"
                label="О себе"
                maxLength={2000}
                value={extraValues.about}
                error={extraErrors.about}
                onChange={(event) =>
                  setExtraValues((prev) => ({ ...prev, about: event.target.value }))
                }
              />
            </div>
          </div>
          <div className="form-actions">
            <Button type="submit" size="inline" disabled={addResume.isPending}>
              {addResume.isPending ? 'Сохраняем…' : 'Сохранить ещё одно'}
            </Button>
            <Button type="button" variant="ghost" size="inline" onClick={() => setExtraOpen(false)}>
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
