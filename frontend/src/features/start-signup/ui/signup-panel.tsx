import { useState } from 'react'
import type { FormEvent } from 'react'
import { useNavigate } from 'react-router'
import { BRAND, ROUTES } from '@/shared/config'
import { isEmail } from '@/shared/lib'
import { Button, TextField } from '@/shared/ui'
import { PANEL } from '../config/content'
import './signup-panel.css'

export function SignupPanel() {
  const navigate = useNavigate()
  const [email, setEmail] = useState('')
  const [error, setError] = useState('')

  const onSubmit = (e: FormEvent<HTMLFormElement>) => {
    e.preventDefault()
    const submitter = (e.nativeEvent as SubmitEvent).submitter as HTMLButtonElement | null
    const role = submitter?.value === 'employer' ? 'employer' : 'candidate'
    const value = email.trim()

    if (!value) return setError(PANEL.emailEmpty)
    if (!isEmail(value)) return setError(PANEL.emailInvalid)

    setError('')
    const target = role === 'employer' ? ROUTES.employerAuth : ROUTES.candidateAuth
    navigate(`${target}?${new URLSearchParams({ email: value, mode: 'register' })}`)
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
        <TextField
          id="email"
          label={PANEL.emailLabel}
          hideLabel
          type="email"
          name="email"
          autoComplete="email"
          inputMode="email"
          placeholder={PANEL.emailPlaceholder}
          value={email}
          error={error}
          onChange={(e) => {
            setEmail(e.target.value)
            if (error) setError('')
          }}
        />

        <Button variant="ghost" type="submit" name="role" value="employer">
          {PANEL.employerButton}
        </Button>
        <Button variant="solid" type="submit" name="role" value="specialist">
          {PANEL.specialistButton}
        </Button>
      </form>

      <a className="panel__invite" href={PANEL.invite.href}>
        {PANEL.invite.label}
      </a>
    </div>
  )
}
