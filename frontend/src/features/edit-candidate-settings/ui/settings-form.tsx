import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import {
  FSP_SYNC_LABELS,
  JOB_STATUS_HINTS,
  JOB_STATUS_LABELS,
  JOB_STATUSES,
  candidateApi,
  candidateKeys,
} from '@/entities/candidate'
import type { JobStatus, OwnCandidateDto } from '@/entities/candidate'
import { getErrorMessage } from '@/shared/api'
import { Button, SelectField, TextField } from '@/shared/ui'
import './settings-form.css'

const MAX_FSP_ID = 64

function useRemember() {
  const queryClient = useQueryClient()
  return (next: OwnCandidateDto) => queryClient.setQueryData(candidateKeys.mine(), next)
}

/** Search status: «Не ищу» hides the profile from the bank, the other two keep it visible. */
export function JobStatusForm({ profile }: { profile: OwnCandidateDto }) {
  const remember = useRemember()
  const [status, setStatus] = useState<JobStatus>(profile.jobStatus)
  const [saved, setSaved] = useState(false)

  const save = useMutation({
    mutationFn: candidateApi.setJobStatus,
    onSuccess: (next) => {
      remember(next)
      setSaved(true)
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (status !== profile.jobStatus) save.mutate(status)
  }

  return (
    <form className="settings-form" noValidate onSubmit={onSubmit}>
      <SelectField
        id="settings-status"
        label="Статус поиска"
        value={status}
        onChange={(event) => {
          setStatus(event.target.value as JobStatus)
          setSaved(false)
        }}
      >
        {JOB_STATUSES.map((item) => (
          <option key={item} value={item}>
            {JOB_STATUS_LABELS[item]}
          </option>
        ))}
      </SelectField>
      <p className="form-hint">
        {JOB_STATUS_HINTS[status]} Уже открытые приглашения остаются в любом статусе.
      </p>
      {save.isError && (
        <p className="form-banner" role="alert">
          {getErrorMessage(save.error)}
        </p>
      )}
      {saved && (
        <p className="form-status" role="status">
          Статус сохранён.
        </p>
      )}
      <div className="form-actions">
        <Button
          type="submit"
          size="inline"
          disabled={save.isPending || status === profile.jobStatus}
        >
          {save.isPending ? 'Сохраняем…' : 'Сохранить статус'}
        </Button>
      </div>
    </form>
  )
}

/** The FSP member id; results arrive once the registry integration is connected. */
export function FspLinkForm({ profile }: { profile: OwnCandidateDto }) {
  const remember = useRemember()
  const [fspId, setFspId] = useState(profile.fspMemberId ?? '')
  const [error, setError] = useState('')
  const [saved, setSaved] = useState(false)

  const save = useMutation({
    mutationFn: (nextId: string) =>
      nextId ? candidateApi.linkFsp(nextId) : candidateApi.unlinkFsp(),
    onSuccess: (next) => {
      remember(next)
      setFspId(next.fspMemberId ?? '')
      setSaved(true)
    },
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const nextId = fspId.trim()
    if (nextId.length > MAX_FSP_ID) {
      setError(`Не длиннее ${MAX_FSP_ID} символов`)
      document.getElementById('settings-fsp')?.focus()
      return
    }
    setError('')
    if (nextId === (profile.fspMemberId ?? '')) return
    save.mutate(nextId)
  }

  return (
    <form className="settings-form" noValidate onSubmit={onSubmit}>
      <TextField
        id="settings-fsp"
        label="ID участника ФСП"
        value={fspId}
        error={error}
        onChange={(event) => {
          setFspId(event.target.value)
          setError('')
          setSaved(false)
        }}
      />
      <p className="form-hint">
        {profile.fspSync ? `Ответ при регистрации: «${FSP_SYNC_LABELS[profile.fspSync]}». ` : ''}
        Синхронизация в разработке: реестр ФСП ещё не подключён, ID сохранится до запуска. Пустое
        поле отвязывает профиль.{' '}
        <a href="https://fsp-russia.ru" target="_blank" rel="noreferrer">
          Федерация спортивного программирования
        </a>
      </p>
      {save.isError && (
        <p className="form-banner" role="alert">
          {getErrorMessage(save.error)}
        </p>
      )}
      {saved && (
        <p className="form-status" role="status">
          {profile.fspMemberId ? 'ID участника сохранён.' : 'Профиль отвязан от ФСП.'}
        </p>
      )}
      <div className="form-actions">
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : 'Сохранить ID'}
        </Button>
      </div>
    </form>
  )
}
