import { useState } from 'react'
import type { FormEvent, ReactNode } from 'react'
import { Button, Modal, TextArea } from '@/shared/ui'

type Props = {
  title: string
  confirmLabel: string
  /** False: the reason may stay empty (e.g. an approval comment). */
  required?: boolean
  label?: string
  pending?: boolean
  error?: string | null
  children?: ReactNode
  onConfirm: (reason: string) => void
  onClose: () => void
}

const MIN_REASON = 3

/** Every moderation action asks why: the answer goes to the journal. */
export function ReasonDialog({
  title,
  confirmLabel,
  required = true,
  label = 'Причина',
  pending,
  error,
  children,
  onConfirm,
  onClose,
}: Props) {
  const [reason, setReason] = useState('')
  const [touched, setTouched] = useState(false)
  const invalid = required && reason.trim().length < MIN_REASON

  const submit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    setTouched(true)
    if (!invalid) onConfirm(reason.trim())
  }

  return (
    <Modal title={title} onClose={onClose}>
      <form className="admin-form" noValidate onSubmit={submit}>
        {children}
        <TextArea
          id="admin-reason"
          label={required ? `${label} (обязательно)` : label}
          value={reason}
          maxLength={2000}
          error={touched && invalid ? 'Опишите причину: она попадёт в журнал' : undefined}
          onChange={(event) => setReason(event.target.value)}
        />
        {error && (
          <p className="admin-error" role="alert">
            {error}
          </p>
        )}
        <div className="admin-form__actions">
          <Button type="submit" size="inline" disabled={pending}>
            {pending ? 'Сохраняем…' : confirmLabel}
          </Button>
          <Button variant="ghost" size="inline" disabled={pending} onClick={onClose}>
            Отмена
          </Button>
        </div>
      </form>
    </Modal>
  )
}
