import { useEffect, useRef, useState } from 'react'
import type { FormEvent } from 'react'
import { getErrorMessage } from '@/shared/api'
import { Button, TextField } from '@/shared/ui'
import { validateAuthForm } from '../model/schema'
import type { AuthFieldErrors, AuthFormValues, AuthMode } from '../model/schema'
import { useAuthSubmit } from '../model/use-auth-submit'
import { EmailVerification } from './email-verification'
import './auth-form.css'

type Props = {
  role: 'candidate' | 'employer'
  initialEmail?: string
  initialMode?: AuthMode
  onModeChange?: (mode: AuthMode) => void
  onSuccess: () => void
}

const MODE_LABELS: Record<AuthMode, string> = { 'sign-in': 'Вход', 'sign-up': 'Регистрация' }

export function AuthForm({
  role,
  initialEmail = '',
  initialMode = 'sign-in',
  onModeChange,
  onSuccess,
}: Props) {
  const [mode, setMode] = useState<AuthMode>(initialMode)
  const [values, setValues] = useState<AuthFormValues>({
    email: initialEmail,
    password: '',
    personalDataConsent: false,
  })
  const [errors, setErrors] = useState<AuthFieldErrors>({})
  const passwordRef = useRef<HTMLInputElement>(null)

  // The email already came from the landing form: continue from the next empty field.
  useEffect(() => {
    if (initialEmail) passwordRef.current?.focus()
  }, [initialEmail])
  const { submit, verification, closeVerification, finishVerification } = useAuthSubmit(
    role,
    onSuccess,
  )

  const update = <K extends keyof AuthFormValues>(key: K, value: AuthFormValues[K]) => {
    setValues((prev) => ({ ...prev, [key]: value }))
    if (errors[key]) setErrors((prev) => ({ ...prev, [key]: undefined }))
  }

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const nextErrors = validateAuthForm(mode, values)
    setErrors(nextErrors)
    if (Object.keys(nextErrors).length === 0) submit.mutate({ mode, values })
  }

  return (
    <div className="auth-form">
      <div className="auth-form__tabs" role="tablist" aria-label="Режим авторизации">
        {(['sign-in', 'sign-up'] as const).map((item) => (
          <button
            key={item}
            type="button"
            role="tab"
            aria-selected={mode === item}
            className={`auth-form__tab${mode === item ? ' is-active' : ''}`}
            onClick={() => {
              setMode(item)
              onModeChange?.(item)
            }}
          >
            {MODE_LABELS[item]}
          </button>
        ))}
      </div>

      <form className="auth-form__form" noValidate onSubmit={onSubmit}>
        <TextField
          id="auth-email"
          label="Электронная почта"
          type="email"
          autoComplete="email"
          value={values.email}
          error={errors.email}
          onChange={(e) => update('email', e.target.value)}
        />
        <TextField
          id="auth-password"
          label="Пароль"
          type="password"
          autoComplete={mode === 'sign-in' ? 'current-password' : 'new-password'}
          ref={passwordRef}
          value={values.password}
          error={errors.password}
          onChange={(e) => update('password', e.target.value)}
        />

        {mode === 'sign-up' && (
          <label className="auth-form__consent">
            <input
              type="checkbox"
              checked={values.personalDataConsent}
              aria-invalid={errors.personalDataConsent ? true : undefined}
              onChange={(e) => update('personalDataConsent', e.target.checked)}
            />
            <span>
              Даю согласие на обработку персональных данных в соответствии с 152-ФЗ
              {errors.personalDataConsent && (
                <strong className="auth-form__consent-error" role="alert">
                  {errors.personalDataConsent}
                </strong>
              )}
            </span>
          </label>
        )}

        {submit.isError && (
          <p className="auth-form__error" role="alert">
            {getErrorMessage(submit.error)}
          </p>
        )}

        <Button type="submit" disabled={submit.isPending}>
          {submit.isPending ? 'Отправка…' : MODE_LABELS[mode]}
        </Button>
      </form>

      {verification && (
        <EmailVerification
          email={verification.email}
          onClose={closeVerification}
          onVerified={finishVerification}
        />
      )}
    </div>
  )
}
