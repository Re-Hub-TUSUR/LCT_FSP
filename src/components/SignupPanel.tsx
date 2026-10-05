import { useState } from 'react'
import type { FormEvent } from 'react'
import { BRAND, PANEL } from '../content.ts'

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

export default function SignupPanel() {
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const submitter = (e.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null
    const role = submitter?.value ?? 'specialist'
    const value = email.trim()

    if (!value) return setError(PANEL.emailEmpty)
    if (!EMAIL_RE.test(value)) return setError(PANEL.emailInvalid)

    setError('')
    // No backend yet — hand-off point for the auth flow
    console.info('signup', { email: value, role })
  }

  return (
    <div className="panel" id="join">
      <span className="chip">
        <span className="chip__bracket">[</span> {PANEL.chip}{' '}
        <span className="chip__bracket">]</span>
      </span>

      <h1 className="panel__title">{BRAND}</h1>
      <p className="panel__tagline">{PANEL.tagline}</p>

      <form className="form" action="#" method="post" noValidate onSubmit={onSubmit}>
        <div className="field">
          <label className="visually-hidden" htmlFor="email">
            {PANEL.emailLabel}
          </label>
          <input
            id="email"
            className="field__input"
            type="email"
            name="email"
            autoComplete="email"
            inputMode="email"
            placeholder={PANEL.emailPlaceholder}
            value={email}
            aria-invalid={error ? true : undefined}
            aria-describedby={error ? 'email-error' : undefined}
            onChange={(e) => {
              setEmail(e.target.value)
              if (error) setError('')
            }}
          />
          <p id="email-error" className="field__error" role="alert">
            {error}
          </p>
        </div>

        <button className="btn btn--ghost" type="submit" name="role" value="employer">
          {PANEL.employerButton}
        </button>
        <button className="btn btn--solid" type="submit" name="role" value="specialist">
          {PANEL.specialistButton}
        </button>
      </form>

      <a className="panel__invite" href={PANEL.invite.href}>
        {PANEL.invite.label}
      </a>
    </div>
  )
}
