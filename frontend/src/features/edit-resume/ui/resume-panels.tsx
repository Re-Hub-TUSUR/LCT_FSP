import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Link } from 'react-router'
import {
  candidateApi,
  candidateKeys,
  dropPhotoUrl,
  FSP_DISCIPLINE_LABELS,
  JOB_STATUS_LABELS,
} from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { categoryQueries } from '@/entities/category'
import { useSession } from '@/entities/session'
import { EMPLOYMENT_LABELS, SALARY_NOTE, WORK_FORMAT_LABELS } from '@/entities/vacancy'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { formatDate, formatRubRange } from '@/shared/lib'
import { Button, ChipList, DataRows, Panel } from '@/shared/ui'
import type { DataRow } from '@/shared/ui'
import { photoFileError, resumeFileError } from '../model/files'
import {
  changedPanels,
  PANEL_FIELDS,
  PANEL_TITLES,
  PANELS,
  panelsPayload,
  validatePanels,
} from '../model/panels'
import type { PanelId } from '../model/panels'
import { applyResumeDraft, RESUME_FIELD_IDS, resumeValuesFrom } from '../model/schema'
import type { ResumeErrors, ResumeValues } from '../model/schema'
import { ExtraResumes } from './extra-resumes'
import { PanelFields } from './panel-fields'
import { PhotoField } from './photo-field'
import './resume-form.css'

const LEVEL_LABELS = {
  regional: 'региональный',
  national: 'всероссийский',
  international: 'международный',
} as const

function monthLabel(value: string): string {
  const [year, month] = value.split('-')
  return month && year ? `${month}.${year}` : value
}

function yearsLabel(years: number): string {
  const tail = years % 10
  const tens = years % 100
  if (tail === 1 && tens !== 11) return `${years} год`
  if (tail >= 2 && tail <= 4 && (tens < 12 || tens > 14)) return `${years} года`
  return `${years} лет`
}

function LockIcon() {
  return (
    <svg className="resume-lock" viewBox="0 0 16 16" width="14" height="14" aria-hidden="true">
      <rect x="3" y="7" width="10" height="7" fill="none" stroke="currentColor" strokeWidth="1.4" />
      <path d="M5.5 7V5a2.5 2.5 0 0 1 5 0v2" fill="none" stroke="currentColor" strokeWidth="1.4" />
    </svg>
  )
}

type Props = { profile: OwnCandidateDto }

/** Saved resume as read-only panels; «Изменить» opens one panel's form in place. */
export function ResumePanels({ profile }: Props) {
  const queryClient = useQueryClient()
  const { user } = useSession()
  const dictionary = useQuery(categoryQueries.dictionary())
  const [editing, setEditing] = useState<PanelId[]>([])
  const [fromFile, setFromFile] = useState(false)
  const [values, setValues] = useState<ResumeValues>(() => resumeValuesFrom(profile))
  const [errors, setErrors] = useState<ResumeErrors>({})
  const [formError, setFormError] = useState('')
  const [notice, setNotice] = useState('')
  const [fileError, setFileError] = useState('')
  const [photoError, setPhotoError] = useState('')

  const remember = (next: OwnCandidateDto) => queryClient.setQueryData(candidateKeys.mine(), next)

  const close = () => {
    setEditing([])
    setFromFile(false)
    setErrors({})
    setFormError('')
  }

  const save = useMutation({
    mutationFn: candidateApi.updateProfile,
    onSuccess: (next) => {
      remember(next)
      setValues(resumeValuesFrom(next))
      close()
      setNotice('Сохранено.')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const upload = useMutation({
    mutationFn: candidateApi.uploadResume,
    onSuccess: (draft) => {
      const before = resumeValuesFrom(profile)
      const after = applyResumeDraft(before, draft)
      const panels = changedPanels(before, after)
      setFileError('')
      setErrors({})
      setFormError('')
      if (panels.length === 0) {
        setNotice('В файле не нашлось ничего нового — профиль не изменился.')
        return
      }
      setNotice('')
      setValues(after)
      setEditing(panels)
      setFromFile(true)
    },
    onError: (error) => setFileError(getErrorMessage(error)),
  })

  const uploadPhoto = useMutation({
    mutationFn: candidateApi.uploadPhoto,
    onSuccess: (next) => {
      remember(next)
      dropPhotoUrl(next.id)
      setPhotoError('')
      void queryClient.invalidateQueries({ queryKey: [...candidateKeys.all, 'photo', next.id] })
    },
    onError: (error) => setPhotoError(getErrorMessage(error)),
  })

  const update = <K extends keyof ResumeValues>(key: K, value: ResumeValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const open = (panel: PanelId) => {
    setValues(resumeValuesFrom(profile))
    setEditing([panel])
    setFromFile(false)
    setErrors({})
    setFormError('')
    setNotice('')
  }

  const cancel = () => {
    setValues(resumeValuesFrom(profile))
    close()
  }

  const submit = () => {
    const panels = PANELS.filter((panel) => editing.includes(panel))
    const next = validatePanels(values, panels)
    setErrors(next)
    const first = panels.flatMap((panel) => PANEL_FIELDS[panel]).find((field) => next[field])
    if (first) {
      document.getElementById(RESUME_FIELD_IDS[first])?.focus()
      return
    }
    save.mutate(panelsPayload(values, panels))
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    submit()
  }

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
    uploadPhoto.mutate(file)
  }

  const specCode = profile.specialization ?? profile.category?.specialization ?? null
  const specLabel =
    dictionary.data?.specializations.find((item) => item.code === specCode)?.label ?? specCode

  const read: Record<PanelId, ReactNode> = {
    basic: (
      <DataRows
        rows={[
          { key: 'name', label: 'Имя и фамилия', value: profile.displayName },
          { key: 'headline', label: 'Должность', value: profile.headline },
          { key: 'spec', label: 'Специализация', value: specLabel },
          { key: 'city', label: 'Город', value: profile.city },
          {
            key: 'birth',
            label: 'Дата рождения',
            value: profile.birthDate ? formatDate(profile.birthDate) : null,
            note: 'Видите только вы. Работодатель увидит лишь пометку, если вам нет 18.',
          },
        ]}
      />
    ),
    search: (
      <DataRows
        rows={[
          {
            key: 'status',
            label: 'Статус поиска',
            value: JOB_STATUS_LABELS[profile.jobStatus],
          },
          {
            key: 'salary',
            label: 'Зарплата',
            value: profile.salaryExpectation
              ? `от ${formatRubRange(profile.salaryExpectation, profile.salaryExpectation)}`
              : null,
            note: profile.salaryExpectation ? SALARY_NOTE : undefined,
          },
          {
            key: 'formats',
            label: 'Формат работы',
            value: profile.workFormats.map((format) => WORK_FORMAT_LABELS[format]).join(', '),
          },
          {
            key: 'employment',
            label: 'Занятость',
            value: profile.employmentTypes.map((type) => EMPLOYMENT_LABELS[type]).join(', '),
          },
          {
            key: 'relocation',
            label: 'Переезд',
            value: profile.relocationReady ? 'Готов к переезду' : 'Не готов',
          },
        ]}
      />
    ),
    experience: profile.noExperience ? (
      <p className="resume-panels__text">Нет опыта работы.</p>
    ) : (
      <DataRows
        rows={[
          ...(profile.experienceYears !== null
            ? [{ key: 'years', label: 'Стаж', value: yearsLabel(profile.experienceYears) }]
            : []),
          ...profile.experienceEntries.map<DataRow>((entry, index) => ({
            key: `job-${index}`,
            label: `${monthLabel(entry.start)} — ${entry.end ? monthLabel(entry.end) : 'сейчас'}`,
            value: `${entry.position}, ${entry.company}`,
            note: entry.stack.length > 0 ? entry.stack.join(', ') : undefined,
          })),
        ]}
      />
    ),
    skills: (
      <DataRows
        rows={[
          {
            key: 'stack',
            label: 'Стек',
            value: <ChipList items={profile.stack} label="Стек" />,
          },
          {
            key: 'soft',
            label: 'Софт-скиллы',
            value:
              profile.softSkills.length > 0 ? (
                <ChipList items={profile.softSkills} label="Софт-скиллы" />
              ) : null,
          },
        ]}
      />
    ),
    education:
      profile.education.length === 0 ? (
        <p className="resume-panels__text resume-panels__text--dim">Образование не указано.</p>
      ) : (
        <DataRows
          rows={profile.education.map((entry, index) => ({
            key: `edu-${index}`,
            label: entry.year ? String(entry.year) : 'Год не указан',
            value: entry.institution,
            note: entry.specialty ?? undefined,
          }))}
        />
      ),
    about: profile.about ? (
      <p className="resume-panels__text">{profile.about}</p>
    ) : (
      <p className="resume-panels__text resume-panels__text--dim">
        Пара фраз о том, чем вы занимаетесь и что ищете, помогает работодателю решить быстрее.
      </p>
    ),
    contacts: (
      <>
        <DataRows
          rows={[
            {
              key: 'email',
              label: 'Email',
              value: user?.email ?? profile.contacts?.email,
              note: (
                <>
                  <LockIcon /> Из аккаунта, здесь не меняется
                </>
              ),
            },
            { key: 'phone', label: 'Телефон', value: profile.contacts?.phone },
            {
              key: 'telegram',
              label: 'Telegram',
              value: profile.contacts?.telegram ? `@${profile.contacts.telegram}` : null,
            },
            { key: 'github', label: 'GitHub', value: profile.githubUrl },
          ]}
        />
        <p className="form-hint">
          Работодатель увидит контакты, только когда вы примете приглашение или откликнетесь.
        </p>
      </>
    ),
  }

  const busy = save.isPending

  return (
    <div className="resume-panels">
      <div className="resume-panels__file">
        <label className="btn btn--ghost btn--inline file-btn">
          {upload.isPending ? 'Читаем файл…' : 'Заполнить из файла'}
          <input
            type="file"
            accept=".pdf,.docx,application/pdf,application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            disabled={upload.isPending || busy}
            onChange={(event) => {
              void onFile(event.target.files?.[0])
              event.target.value = ''
            }}
          />
        </label>
        <p className="form-hint">
          PDF или DOCX до 5 МБ. Файл не сохраняется: распознанные поля откроются для проверки.
        </p>
      </div>
      {fileError && (
        <p className="form-banner" role="alert">
          {fileError}
        </p>
      )}
      {notice && (
        <p className="form-status" role="status">
          {notice}
        </p>
      )}

      {fromFile && (
        <div className="resume-panels__draft" role="region" aria-label="Данные из файла">
          <p className="resume-start__lead">Проверьте распознанные поля</p>
          <p className="form-hint">
            Из файла изменились разделы:{' '}
            {editing.map((panel) => PANEL_TITLES[panel].toLowerCase()).join(', ')}. Ничего не
            сохранено, пока вы не нажмёте «Сохранить всё».
          </p>
          {formError && (
            <p className="form-banner" role="alert">
              {formError}
            </p>
          )}
          <div className="form-actions">
            <Button type="button" size="inline" disabled={busy} onClick={submit}>
              {busy ? 'Сохраняем…' : 'Сохранить всё'}
            </Button>
            <Button type="button" variant="ghost" size="inline" disabled={busy} onClick={cancel}>
              Отменить
            </Button>
          </div>
        </div>
      )}

      {PANELS.map((panel) => {
        const isOpen = editing.includes(panel)
        return (
          <Panel
            key={panel}
            title={PANEL_TITLES[panel]}
            className={isOpen ? 'is-editing' : undefined}
            action={
              !isOpen && editing.length === 0 ? (
                <button type="button" className="panel-edit" onClick={() => open(panel)}>
                  Изменить
                </button>
              ) : undefined
            }
          >
            {isOpen ? (
              <form className="resume-form" noValidate onSubmit={onSubmit}>
                <PanelFields panel={panel} values={values} errors={errors} update={update} />
                {!fromFile && (
                  <>
                    {formError && (
                      <p className="form-banner" role="alert">
                        {formError}
                      </p>
                    )}
                    <div className="form-actions">
                      <Button type="submit" size="inline" disabled={busy}>
                        {busy ? 'Сохраняем…' : 'Сохранить'}
                      </Button>
                      <Button
                        type="button"
                        variant="ghost"
                        size="inline"
                        disabled={busy}
                        onClick={cancel}
                      >
                        Отмена
                      </Button>
                    </div>
                  </>
                )}
              </form>
            ) : (
              read[panel]
            )}
          </Panel>
        )
      })}

      <Panel title="Фото">
        <PhotoField
          candidateId={profile.id}
          hasPhoto={profile.hasPhoto === true}
          previewUrl={null}
          error={photoError}
          busy={uploadPhoto.isPending}
          onPick={(file) => void onPhoto(file)}
        />
      </Panel>

      <Panel title="Дополнительные резюме">
        <ExtraResumes profile={profile} />
      </Panel>

      <Panel title="Достижения ФСП">
        {profile.fspAchievements.length > 0 ? (
          <DataRows
            rows={profile.fspAchievements.map((item, index) => ({
              key: `fsp-${index}`,
              label: String(item.year),
              value: item.eventName,
              note: `${item.place ? `${item.place} место` : 'участие'} · ${FSP_DISCIPLINE_LABELS[item.discipline]} · ${LEVEL_LABELS[item.level]}`,
            }))}
          />
        ) : (
          <p className="resume-panels__text resume-panels__text--dim">
            {profile.fspLinked
              ? 'В ФСП пока нет результатов по вашему ID.'
              : 'Профиль не связан с ФСП.'}
          </p>
        )}
        <p className="form-hint">
          <LockIcon /> Достижения приходят из ФСП, вручную их не изменить.{' '}
          {!profile.fspLinked && <Link to={ROUTES.profileSettings}>Связать в настройках</Link>}
        </p>
      </Panel>
    </div>
  )
}
