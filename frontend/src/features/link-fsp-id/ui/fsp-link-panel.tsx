import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useState } from 'react'
import { FSP_SYNC_LABELS, candidateApi, candidateKeys } from '@/entities/candidate'
import type { OwnCandidateDto } from '@/entities/candidate'
import { getErrorMessage } from '@/shared/api'
import { formatDateTime } from '@/shared/lib'
import { Button, ConfirmDialog, DataRows } from '@/shared/ui'
import { fspCallbackUri, goToFspId } from '../lib/callback-uri'
import './fsp-link-panel.css'

function plural(count: number, one: string, few: string, many: string): string {
  const tens = count % 100
  const units = count % 10
  if (tens >= 11 && tens <= 14) return many
  if (units === 1) return one
  if (units >= 2 && units <= 4) return few
  return many
}

function importedText(profile: OwnCandidateDto): string {
  const results = profile.fspAchievements?.length ?? 0
  const titles = profile.fspTitles?.length ?? 0
  if (results === 0 && titles === 0) {
    return 'В реестре ФСП пока нет ваших результатов. Профиль работает как обычно: категорию задают тест и опыт.'
  }
  const parts = [`${results} ${plural(results, 'результат', 'результата', 'результатов')}`]
  if (titles > 0) parts.push(`${titles} ${plural(titles, 'звание', 'звания', 'званий')}`)
  return `Выгружено из реестра: ${parts.join(' и ')}.`
}

/** Sends the browser to FSP ID; it comes back to `/profile/fsp/callback`. */
export function useStartFspLink() {
  return useMutation({
    mutationFn: () => candidateApi.authorizeFsp(fspCallbackUri()),
    onSuccess: ({ authorizeUrl }) => goToFspId(authorizeUrl),
  })
}

type Props = {
  profile: OwnCandidateDto
  /** Shown once after the return from FSP ID. */
  justLinked?: boolean
}

/**
 * The profile is linked by signing in to FSP ID (OIDC), never by typing an id: the federation
 * confirms who the candidate is, and the registry sends the results.
 */
export function FspLinkPanel({ profile, justLinked = false }: Props) {
  const queryClient = useQueryClient()
  const [confirmUnlink, setConfirmUnlink] = useState(false)
  const remember = (next: OwnCandidateDto) => queryClient.setQueryData(candidateKeys.mine(), next)

  const start = useStartFspLink()
  const sync = useMutation({ mutationFn: candidateApi.syncFsp, onSuccess: remember })
  const unlink = useMutation({
    mutationFn: candidateApi.unlinkFsp,
    onSuccess: (next) => {
      remember(next)
      setConfirmUnlink(false)
    },
  })
  const failure = start.error ?? sync.error ?? unlink.error

  if (!profile.fspMemberId) {
    return (
      <div className="fsp-link">
        <p className="form-hint">
          {profile.fspSync ? `Ответ при регистрации: «${FSP_SYNC_LABELS[profile.fspSync]}». ` : ''}
          Войдите через ФСП ID — платформа получит ваш номер участника и результаты из реестра
          Федерации. Результаты поднимают вас внутри категории и не меняют грейд. Вход на платформу
          остаётся по email.{' '}
          <a href="https://fsp-russia.ru" target="_blank" rel="noreferrer">
            Федерация спортивного программирования
          </a>
        </p>
        {failure && (
          <p className="form-banner" role="alert">
            {getErrorMessage(failure)}
          </p>
        )}
        <div className="form-actions">
          <Button size="inline" disabled={start.isPending} onClick={() => start.mutate()}>
            {start.isPending ? 'Переходим в ФСП ID…' : 'Привязать ФСП ID'}
          </Button>
        </div>
      </div>
    )
  }

  return (
    <div className="fsp-link">
      {justLinked && (
        <p className="form-status" role="status">
          ФСП ID привязан.
        </p>
      )}
      <DataRows
        rows={[
          {
            key: 'id',
            label: 'Участник ФСП',
            value: profile.fspMemberId,
            note: profile.fspLinkedAt
              ? `Подтверждён через ФСП ID ${formatDateTime(profile.fspLinkedAt)}`
              : 'Подтверждён через ФСП ID',
          },
          {
            key: 'sync',
            label: 'Реестр ФСП',
            value: profile.fspSyncedAt
              ? `Обновлено ${formatDateTime(profile.fspSyncedAt)}`
              : 'Ещё не выгружено',
            note: profile.fspSyncedAt ? importedText(profile) : undefined,
          },
        ]}
      />
      {profile.fspSyncError && (
        <p className="form-banner" role="alert">
          {profile.fspSyncError}. Связь сохранена — обновите данные позже.
        </p>
      )}
      {failure && (
        <p className="form-banner" role="alert">
          {getErrorMessage(failure)}
        </p>
      )}
      <div className="fsp-link__actions">
        <Button size="inline" disabled={sync.isPending} onClick={() => sync.mutate()}>
          {sync.isPending ? 'Обновляем…' : 'Обновить из реестра'}
        </Button>
        <Button
          size="inline"
          variant="ghost"
          disabled={start.isPending}
          onClick={() => start.mutate()}
        >
          Войти другим участником
        </Button>
        <Button size="inline" variant="ghost" onClick={() => setConfirmUnlink(true)}>
          Отвязать
        </Button>
      </div>
      {confirmUnlink && (
        <ConfirmDialog
          title="Отвязать ФСП ID?"
          confirmLabel={unlink.isPending ? 'Отвязываем…' : 'Отвязать'}
          busy={unlink.isPending}
          onConfirm={() => unlink.mutate()}
          onCancel={() => setConfirmUnlink(false)}
        >
          Результаты ФСП пропадут из профиля и перестанут влиять на порядок в выдаче. Привязать
          снова можно в любой момент.
        </ConfirmDialog>
      )}
    </div>
  )
}
