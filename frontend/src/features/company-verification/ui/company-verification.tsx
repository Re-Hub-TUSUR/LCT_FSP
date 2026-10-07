import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { getErrorMessage } from '@/shared/api'
import { formatDate } from '@/shared/lib'
import { Button, ErrorState, Loader, Section } from '@/shared/ui'
import { verificationApi, verificationKeys, verificationQueries } from '../api/verification-api'
import type { CompanyVerificationDto, VerificationStatus } from '../api/verification-api'
import './company-verification.css'

const MAX_SIZE = 10 * 1024 * 1024

const STATUS_TEXT: Record<VerificationStatus, string> = {
  pending: 'Документы на проверке у администратора',
  approved: 'Компания подтверждена',
  rejected: 'Заявка отклонена',
}

/**
 * Official documents of the company (PDF): an admin checks them and confirms the company is
 * real. Uploading after a rejection sends a new request.
 */
export function CompanyVerification() {
  const queryClient = useQueryClient()
  const input = useRef<HTMLInputElement>(null)
  const [tooBig, setTooBig] = useState(false)
  const state = useQuery(verificationQueries.mine())
  const done = (data: CompanyVerificationDto) =>
    queryClient.setQueryData(verificationKeys.mine, data)
  const upload = useMutation({ mutationFn: verificationApi.upload, onSuccess: done })
  const remove = useMutation({ mutationFn: verificationApi.remove, onSuccess: done })

  const pick = (files: FileList | null) => {
    const file = files?.[0]
    if (input.current) input.current.value = ''
    if (!file) return
    upload.reset()
    if (file.size > MAX_SIZE) {
      setTooBig(true)
      return
    }
    setTooBig(false)
    upload.mutate(file)
  }

  return (
    <Section title="Подтверждение компании">
      {state.isPending ? (
        <Loader />
      ) : state.isError ? (
        <ErrorState message={getErrorMessage(state.error)} onRetry={() => void state.refetch()} />
      ) : (
        <div className="verification-box">
          <p
            className={`verification-box__status verification-box__status--${state.data.status ?? 'none'}`}
          >
            {state.data.status ? STATUS_TEXT[state.data.status] : 'Документы ещё не загружены'}
            {state.data.decidedAt && ` · ${formatDate(state.data.decidedAt)}`}
          </p>
          {state.data.status === 'rejected' && state.data.reason && (
            <p className="verification-box__reason">Причина: {state.data.reason}</p>
          )}
          <p className="verification-box__hint">
            Загрузите официальные документы компании в PDF (до 10 МБ): выписку из ЕГРЮЛ,
            свидетельство ИНН/ОГРН или письмо на бланке. Администратор сверит их с профилем.
          </p>
          {state.data.documents.length > 0 && (
            <ul className="verification-box__files">
              {state.data.documents.map((document) => (
                <li key={document.id}>
                  <span>{document.filename}</span>
                  <span className="verification-box__meta">
                    {Math.max(1, Math.round(document.sizeBytes / 1024))} КБ ·{' '}
                    {formatDate(document.uploadedAt)}
                  </span>
                  {state.data.status !== 'approved' && (
                    <button
                      type="button"
                      className="verification-box__remove"
                      disabled={remove.isPending}
                      onClick={() => remove.mutate(document.id)}
                    >
                      Удалить
                    </button>
                  )}
                </li>
              ))}
            </ul>
          )}
          <input
            ref={input}
            className="visually-hidden"
            type="file"
            accept="application/pdf,.pdf"
            aria-label="PDF-документ компании"
            onChange={(event) => pick(event.target.files)}
          />
          <Button
            variant="ghost"
            size="inline"
            disabled={upload.isPending}
            onClick={() => input.current?.click()}
          >
            {upload.isPending ? 'Загружаем…' : 'Загрузить PDF'}
          </Button>
          {tooBig && (
            <p className="verification-box__error" role="alert">
              Файл больше 10 МБ
            </p>
          )}
          {(upload.isError || remove.isError) && (
            <p className="verification-box__error" role="alert">
              {getErrorMessage(upload.error ?? remove.error)}
            </p>
          )}
        </div>
      )}
    </Section>
  )
}
