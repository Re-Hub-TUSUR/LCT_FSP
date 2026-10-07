import { useMutation } from '@tanstack/react-query'
import { useState } from 'react'
import type { FormEvent } from 'react'
import { sessionStore, useSession } from '@/entities/session'
import { userApi } from '@/entities/user'
import type { UserDto } from '@/entities/user'
import { getErrorMessage } from '@/shared/api'
import { Button, TextField } from '@/shared/ui'
import './owner-form.css'

type Values = { firstName: string; lastName: string; phone: string }
type Errors = Partial<Record<keyof Values, string>>

const PHONE = /^\+?[\d\s()-]{10,20}$/

function validate(values: Values): Errors {
  const errors: Errors = {}
  if (!values.firstName.trim()) errors.firstName = 'Укажите имя'
  if (!values.lastName.trim()) errors.lastName = 'Укажите фамилию'
  const phone = values.phone.trim()
  if (phone && !PHONE.test(phone)) errors.phone = 'Проверьте номер: +7 900 000-00-00'
  return errors
}

/** Setup step «О вас»: the person who answers candidates. */
export function OwnerForm({
  onSaved,
  submitLabel = 'Далее',
}: {
  onSaved?: (user: UserDto) => void
  submitLabel?: string
}) {
  const { session, user } = useSession()
  const [values, setValues] = useState<Values>({
    firstName: user?.firstName ?? '',
    lastName: user?.lastName ?? '',
    phone: user?.phone ?? '',
  })
  const [errors, setErrors] = useState<Errors>({})

  const save = useMutation({
    mutationFn: userApi.updateMe,
    onSuccess: (next) => {
      if (session) sessionStore.set({ ...session, user: next })
      onSaved?.(next)
    },
  })

  const update = (key: keyof Values, value: string) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const onSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault()
    const next = validate(values)
    setErrors(next)
    const first = (['firstName', 'lastName', 'phone'] as const).find((key) => next[key])
    if (first) {
      document.getElementById(`owner-${first}`)?.focus()
      return
    }
    save.mutate({
      firstName: values.firstName.trim(),
      lastName: values.lastName.trim(),
      phone: values.phone.trim() || null,
    })
  }

  return (
    <form className="owner-form" noValidate onSubmit={onSubmit}>
      <div className="owner-form__grid">
        <TextField
          id="owner-firstName"
          label="Имя"
          autoComplete="given-name"
          value={values.firstName}
          error={errors.firstName}
          onChange={(event) => update('firstName', event.target.value)}
        />
        <TextField
          id="owner-lastName"
          label="Фамилия"
          autoComplete="family-name"
          value={values.lastName}
          error={errors.lastName}
          onChange={(event) => update('lastName', event.target.value)}
        />
        <TextField
          id="owner-phone"
          label="Телефон (необязательно)"
          type="tel"
          autoComplete="tel"
          placeholder="+7 900 000-00-00"
          value={values.phone}
          error={errors.phone}
          onChange={(event) => update('phone', event.target.value)}
        />
      </div>
      {save.isError && (
        <p className="form-banner" role="alert">
          {getErrorMessage(save.error)}
        </p>
      )}
      {save.isSuccess && !onSaved && (
        <p className="form-status" role="status">
          Сохранено.
        </p>
      )}
      <div className="form-actions">
        <Button type="submit" size="inline" disabled={save.isPending}>
          {save.isPending ? 'Сохраняем…' : submitLabel}
        </Button>
      </div>
    </form>
  )
}
