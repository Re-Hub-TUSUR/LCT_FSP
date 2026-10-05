import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { invitationApi, invitationKeys } from '@/entities/invitation'
import type { InvitationDto } from '@/entities/invitation'
import { getErrorMessage } from '@/shared/api'
import { Button, TextArea, TextField } from '@/shared/ui'
import { inviteSchema } from '../model/schema'
import type { InviteFormErrors, InviteFormValues } from '../model/schema'
import './invite-candidate-form.css'

type Props = {
  candidateId: string
  vacancyId?: string
  onSent?: (invitation: InvitationDto) => void
}

const EMPTY: InviteFormValues = { message: '', salaryFrom: '', salaryTo: '', contactMethod: '' }

export function InviteCandidateForm({ candidateId, vacancyId, onSent }: Props) {
  const queryClient = useQueryClient()
  const [values, setValues] = useState<InviteFormValues>(EMPTY)
  const [errors, setErrors] = useState<InviteFormErrors>({})

  const invite = useMutation({
    mutationFn: invitationApi.create,
    onSuccess: (invitation) => {
      void queryClient.invalidateQueries({ queryKey: invitationKeys.list('outgoing') })
      setValues(EMPTY)
      onSent?.(invitation)
    },
  })

  const update = (key: keyof InviteFormValues, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const result = inviteSchema.safeParse(values)
    if (!result.success) {
      const next: InviteFormErrors = {}
      for (const issue of result.error.issues) {
        const key = issue.path[0] as keyof InviteFormValues
        next[key] ??= issue.message
      }
      return setErrors(next)
    }
    const { message, salaryFrom, salaryTo, contactMethod } = result.data
    invite.mutate({
      candidateId,
      vacancyId,
      message,
      contactMethod,
      salary: { from: salaryFrom, to: salaryTo },
    })
  }

  return (
    <form className="invite-form" noValidate onSubmit={onSubmit} aria-label="Приглашение кандидату">
      <TextArea
        id="invite-message"
        label="Предложение"
        value={values.message}
        error={errors.message}
        onChange={(e) => update('message', e.target.value)}
      />
      <div className="invite-form__row">
        <TextField
          id="invite-salary-from"
          label="Зарплата от, ₽"
          inputMode="numeric"
          value={values.salaryFrom}
          error={errors.salaryFrom}
          onChange={(e) => update('salaryFrom', e.target.value)}
        />
        <TextField
          id="invite-salary-to"
          label="Зарплата до, ₽"
          inputMode="numeric"
          value={values.salaryTo}
          error={errors.salaryTo}
          onChange={(e) => update('salaryTo', e.target.value)}
        />
      </div>
      <TextField
        id="invite-contact"
        label="Способ связи"
        placeholder="Telegram, email или телефон рекрутера"
        value={values.contactMethod}
        error={errors.contactMethod}
        onChange={(e) => update('contactMethod', e.target.value)}
      />

      {invite.isError && (
        <p className="invite-form__status invite-form__status--error" role="alert">
          {getErrorMessage(invite.error)}
        </p>
      )}
      {invite.isSuccess && (
        <p className="invite-form__status" role="status">
          Приглашение отправлено
        </p>
      )}

      <Button type="submit" disabled={invite.isPending}>
        {invite.isPending ? 'Отправка…' : 'Пригласить'}
      </Button>
    </form>
  )
}
