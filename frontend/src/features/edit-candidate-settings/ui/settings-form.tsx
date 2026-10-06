import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { FSP_DISCIPLINE_LABELS, candidateApi, candidateKeys } from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { getErrorMessage } from '@/shared/api'
import { Button, TextField } from '@/shared/ui'
import './settings-form.css'

const LEVELS = {
  regional: 'региональные',
  national: 'всероссийские',
  international: 'международные',
} as const

export function CandidateSettingsForm({ profile }: { profile: OwnCandidateDto }) {
  const queryClient = useQueryClient()
  const [searching, setSearching] = useState(profile.searching)
  const [fspId, setFspId] = useState(profile.fspMemberId ?? '')
  const [fspError, setFspError] = useState('')
  const [formError, setFormError] = useState('')
  const [saved, setSaved] = useState(false)

  const save = useMutation({
    mutationFn: async () => {
      const nextId = fspId.trim()
      if (nextId.length > 64) throw new Error('ID участника ФСП — не длиннее 64 символов')
      let next = profile
      if (searching !== profile.searching) next = await candidateApi.setSearching(searching)
      if (nextId && nextId !== (profile.fspMemberId ?? ''))
        next = await candidateApi.linkFsp(nextId)
      if (!nextId && profile.fspLinked) next = await candidateApi.unlinkFsp()
      return next
    },
    onSuccess: (next) => {
      queryClient.setQueryData(candidateKeys.mine(), next)
      setSaved(true)
      setFormError('')
    },
    onError: (error) => setFormError(getErrorMessage(error)),
  })

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    if (fspId.trim().length > 64) {
      setFspError('Не длиннее 64 символов')
      document.getElementById('settings-fsp')?.focus()
      return
    }
    setFspError('')
    save.mutate()
  }

  return (
    <form className="settings-form" noValidate onSubmit={onSubmit}>
      <label className="check">
        <input
          type="checkbox"
          checked={searching}
          onChange={(event) => {
            setSearching(event.target.checked)
            setSaved(false)
          }}
        />
        Показывать профиль работодателям
      </label>
      <p className="form-hint">
        Выключенный профиль пропадает из банка и подборок. Уже открытые приглашения остаются.
      </p>

      <TextField
        id="settings-fsp"
        label="ID участника ФСП"
        value={fspId}
        error={fspError}
        onChange={(event) => {
          setFspId(event.target.value)
          setFspError('')
          setSaved(false)
        }}
      />
      {profile.fspAchievements.length === 0 ? (
        <p className="form-hint">
          Истории ФСП пока нет. Это не влияет на позицию в выдаче.{' '}
          <a href="https://fsp-russia.ru" target="_blank" rel="noreferrer">
            Федерация спортивного программирования
          </a>
        </p>
      ) : (
        <ul className="settings-form__achievements">
          {profile.fspAchievements.map((item) => (
            <li key={`${item.eventName}-${item.year}`}>
              {item.year} · {item.eventName} · {FSP_DISCIPLINE_LABELS[item.discipline]} ·{' '}
              {LEVELS[item.level]}
              {item.place != null ? ` · ${item.place} место` : ''}
            </li>
          ))}
        </ul>
      )}

      {formError && (
        <p className="form-banner" role="alert">
          {formError}
        </p>
      )}
      {saved && (
        <p className="form-status" role="status">
          Настройки сохранены.
        </p>
      )}

      <div className="form-actions">
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : 'Сохранить'}
        </Button>
      </div>
    </form>
  )
}
