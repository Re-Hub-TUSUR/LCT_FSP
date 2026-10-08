import { useEffect, useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { calendarEventApi, calendarEventKeys } from '@/entities/calendar-event'
import type { CalendarEventDto } from '@/entities/calendar-event'
import { candidateQueries } from '@/entities/candidate'
import { conversationQueries } from '@/entities/conversation'
import { vacancyQueries } from '@/entities/vacancy'
import { getErrorMessage } from '@/shared/api'
import { toDateInput, toTimeInput } from '@/shared/lib'
import { Button, Chip, Modal, SelectField, TextArea, TextField } from '@/shared/ui'
import { DEFAULT_TITLE, DURATIONS, parseMeetingForm } from '../model/form'
import type { MeetingFormErrors, MeetingFormValues } from '../model/form'
import './manage-meeting.css'

type Picked = { id: string; name?: string }

type Props = {
  /** Edit this meeting… */
  event?: CalendarEventDto
  /** …or schedule a new one starting at this local time. */
  start?: Date
  /** Candidate chosen beforehand, e.g. on their profile page. */
  candidateId?: string
  onClose: () => void
}

function initialValues(event?: CalendarEventDto, start = new Date()): MeetingFormValues {
  if (!event) {
    return {
      title: DEFAULT_TITLE,
      date: toDateInput(start),
      time: toTimeInput(start),
      duration: '60',
      vacancyId: '',
      location: '',
      note: '',
    }
  }
  const startsAt = new Date(event.startsAt)
  const minutes = Math.round((new Date(event.endsAt).getTime() - startsAt.getTime()) / 60_000)
  return {
    title: event.title,
    date: toDateInput(startsAt),
    time: toTimeInput(startsAt),
    duration: String(minutes),
    vacancyId: event.vacancy?.id ?? '',
    location: event.location ?? '',
    note: event.note ?? '',
  }
}

type Source = 'all' | 'liked' | 'chats'

type Option = Picked & { hint: string }

const NOTHING: Record<Source, string> = {
  all: 'Никого не нашли. В поиске только кандидаты с подтверждённой категорией — остальных ищите в чатах.',
  liked: 'Среди отобранных никого нет',
  chats: 'Чатов с кандидатами пока нет: они появляются после взаимного интереса',
}

/**
 * Search over the candidate bank; favourites and chats are one tap away. The bank holds only
 * candidates with a confirmed category, so a newcomer is reached through the chat with them.
 */
function CandidatePicker({ onPick, error }: { onPick: (c: Picked) => void; error?: string }) {
  const [text, setText] = useState('')
  const [q, setQ] = useState('')
  const [source, setSource] = useState<Source>('all')

  useEffect(() => {
    const timer = setTimeout(() => setQ(text.trim()), 300)
    return () => clearTimeout(timer)
  }, [text])

  const search = useQuery({
    ...candidateQueries.search({
      q: q || undefined,
      view: source === 'liked' ? 'liked' : 'all',
      perPage: 6,
    }),
    enabled: source !== 'chats',
  })
  const chats = useQuery({ ...conversationQueries.list(), enabled: source === 'chats' })
  const found = source === 'chats' ? chats : search

  const needle = text.trim().toLowerCase()
  const options: Option[] | undefined =
    source === 'chats'
      ? chats.data
          ?.map(({ peer }) => ({ id: peer.id, name: peer.name, hint: peer.subtitle ?? '' }))
          .filter((item) => `${item.name} ${item.hint}`.toLowerCase().includes(needle))
      : search.data?.items.map(({ candidate }) => ({
          id: candidate.id,
          name: candidate.displayName,
          hint: candidate.headline ?? candidate.category?.label ?? '',
        }))

  return (
    <div className="meeting-picker">
      <TextField
        id="meeting-candidate"
        label="Кандидат"
        placeholder="Имя, стек или специализация"
        autoComplete="off"
        value={text}
        error={error}
        onChange={(e) => setText(e.target.value)}
      />
      <div className="meeting-picker__chips">
        <Chip active={source === 'all'} onClick={() => setSource('all')}>
          Все
        </Chip>
        <Chip active={source === 'liked'} onClick={() => setSource('liked')}>
          Отобранные
        </Chip>
        <Chip active={source === 'chats'} onClick={() => setSource('chats')}>
          Из чатов
        </Chip>
      </div>
      <ul className="meeting-picker__list" aria-label="Найденные кандидаты">
        {options?.map((option) => (
          <li key={option.id}>
            <button
              type="button"
              className="meeting-picker__option"
              onClick={() => onPick({ id: option.id, name: option.name })}
            >
              <span>{option.name}</span>
              <span className="meeting-picker__hint">{option.hint}</span>
            </button>
          </li>
        ))}
      </ul>
      {found.isPending && <p className="meeting-form__status">Ищем…</p>}
      {found.isError && (
        <p className="meeting-form__status meeting-form__status--error" role="alert">
          {getErrorMessage(found.error)}
        </p>
      )}
      {options?.length === 0 && <p className="meeting-form__status">{NOTHING[source]}</p>}
    </div>
  )
}

/** Employer's form: schedule a meeting with a candidate or change an existing one. */
export function MeetingFormDialog({ event, start, candidateId, onClose }: Props) {
  const queryClient = useQueryClient()
  const [values, setValues] = useState(() => initialValues(event, start))
  const [errors, setErrors] = useState<MeetingFormErrors>({})
  const [picked, setPicked] = useState<Picked | null>(
    event ? event.candidate : candidateId ? { id: candidateId } : null,
  )

  const vacancies = useQuery(vacancyQueries.mine())
  // Only the id is known when the dialog is opened from a profile page.
  const profile = useQuery({
    ...candidateQueries.detail(picked?.id ?? ''),
    enabled: Boolean(picked && !picked.name),
  })
  const candidateName = picked?.name ?? profile.data?.displayName ?? '…'

  const save = useMutation({
    mutationFn: (payload: Parameters<typeof calendarEventApi.reschedule>[1]) =>
      event
        ? calendarEventApi.reschedule(event.id, payload)
        : calendarEventApi.schedule({ ...payload, candidateId: picked?.id ?? '' }),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: calendarEventKeys.all })
      onClose()
    },
  })

  const update = (key: keyof MeetingFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const result = parseMeetingForm(values)
    const candidate = picked ? undefined : 'Выберите кандидата'
    if (!result.ok || candidate) {
      return setErrors({ ...(result.ok ? {} : result.errors), candidate })
    }
    save.mutate(result.payload)
  }

  const durations = { ...DURATIONS }
  const current = Number(values.duration)
  if (current > 0) durations[current] ??= `${current} мин`

  return (
    <Modal title={event ? 'Изменить встречу' : 'Назначить встречу'} onClose={onClose}>
      <form className="meeting-form" noValidate onSubmit={onSubmit}>
        {picked ? (
          <div className="meeting-form__candidate">
            <div>
              <p className="meeting-form__label">Кандидат</p>
              <p className="meeting-form__value">{candidateName}</p>
            </div>
            {!event && (
              <button type="button" className="meeting-form__link" onClick={() => setPicked(null)}>
                Изменить
              </button>
            )}
          </div>
        ) : (
          <CandidatePicker
            error={errors.candidate}
            onPick={(candidate) => {
              setPicked(candidate)
              setErrors((prev) => ({ ...prev, candidate: undefined }))
            }}
          />
        )}

        <TextField
          id="meeting-title"
          label="Название"
          maxLength={200}
          value={values.title}
          error={errors.title}
          onChange={(e) => update('title', e.target.value)}
        />

        <div className="meeting-form__row">
          <TextField
            id="meeting-date"
            label="Дата"
            type="date"
            value={values.date}
            error={errors.date}
            onChange={(e) => update('date', e.target.value)}
          />
          <TextField
            id="meeting-time"
            label="Начало"
            type="time"
            step={300}
            value={values.time}
            error={errors.time}
            onChange={(e) => update('time', e.target.value)}
          />
          <SelectField
            id="meeting-duration"
            label="Длительность"
            value={values.duration}
            error={errors.duration}
            onChange={(e) => update('duration', e.target.value)}
          >
            {Object.entries(durations).map(([minutes, label]) => (
              <option key={minutes} value={minutes}>
                {label}
              </option>
            ))}
          </SelectField>
        </div>

        <SelectField
          id="meeting-vacancy"
          label="Вакансия"
          value={values.vacancyId}
          onChange={(e) => update('vacancyId', e.target.value)}
        >
          <option value="">Без привязки к вакансии</option>
          {vacancies.data?.items.map((vacancy) => (
            <option key={vacancy.id} value={vacancy.id}>
              {vacancy.title}
            </option>
          ))}
        </SelectField>

        <TextField
          id="meeting-location"
          label="Где"
          placeholder="Ссылка на звонок или адрес офиса"
          maxLength={500}
          value={values.location}
          onChange={(e) => update('location', e.target.value)}
        />

        <TextArea
          id="meeting-note"
          label="Комментарий для кандидата"
          maxLength={2000}
          value={values.note}
          onChange={(e) => update('note', e.target.value)}
        />

        {event && event.status !== 'pending' && (
          <p className="meeting-form__status">
            Если изменить время, кандидату нужно будет ответить заново
          </p>
        )}
        {save.isError && (
          <p className="meeting-form__status meeting-form__status--error" role="alert">
            {getErrorMessage(save.error)}
          </p>
        )}

        <Button type="submit" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : event ? 'Сохранить' : 'Назначить'}
        </Button>
      </form>
    </Modal>
  )
}
