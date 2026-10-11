import { useEffect, useRef, useState } from 'react'
import type { ClipboardEvent, KeyboardEvent as ReactKeyboardEvent } from 'react'
import { createPortal } from 'react-dom'
import { sessionApi } from '@/entities/session'
import { ApiError } from '@/shared/api'
import './email-verification.css'

const SLOTS = [0, 1, 2, 3, 4, 5] as const
const EMPTY: string[] = ['', '', '', '', '', '']

type Props = {
  email: string
  onVerified: () => Promise<void>
  onClose: () => void
}

function maskEmail(email: string) {
  return email.replace(/(.{2})(.*)(@.*)/, '$1***$3')
}

function messageOf(error: unknown, fallback: string) {
  return error instanceof ApiError || error instanceof Error ? error.message : fallback
}

/** Six-digit code dialog. Same interaction as the reference: type, paste, auto-submit, resend. */
export function EmailVerification({ email, onVerified, onClose }: Props) {
  const [code, setCode] = useState(EMPTY)
  const [error, setError] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isResending, setIsResending] = useState(false)
  const [resendCooldown, setResendCooldown] = useState(60)
  const inputRefs = useRef<(HTMLInputElement | null)[]>([])

  useEffect(() => {
    inputRefs.current[0]?.focus()
  }, [])

  useEffect(() => {
    if (resendCooldown <= 0) return undefined
    const timer = setTimeout(() => setResendCooldown((value) => value - 1), 1000)
    return () => clearTimeout(timer)
  }, [resendCooldown])

  useEffect(() => {
    const onKey = (event: globalThis.KeyboardEvent) => {
      if (event.key === 'Escape') onClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [onClose])

  const handleVerify = async (verificationCode: string) => {
    setIsLoading(true)
    setError('')
    try {
      await sessionApi.verifyEmail({ email, code: verificationCode })
      await onVerified()
    } catch (err) {
      setError(messageOf(err, 'Не удалось подтвердить. Проверьте код и попробуйте снова.'))
      setCode(EMPTY)
      inputRefs.current[0]?.focus()
    } finally {
      setIsLoading(false)
    }
  }

  const handleInputChange = (index: number, value: string) => {
    if (value && !/^\d$/.test(value)) return
    const next = [...code]
    next[index] = value
    setCode(next)
    setError('')
    if (value && index < 5) inputRefs.current[index + 1]?.focus()
    if (value && index === 5 && next.every((digit) => digit !== '')) {
      void handleVerify(next.join(''))
    }
  }

  const handleKeyDown = (index: number, event: ReactKeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'Backspace' && !code[index] && index > 0) {
      inputRefs.current[index - 1]?.focus()
    }
  }

  const handlePaste = (event: ClipboardEvent) => {
    event.preventDefault()
    const pasted = event.clipboardData.getData('text').replace(/\D/g, '').slice(0, 6)
    if (pasted.length !== 6) return
    setCode(pasted.split(''))
    inputRefs.current[5]?.focus()
    void handleVerify(pasted)
  }

  const handleResend = async () => {
    if (resendCooldown > 0) return
    setIsResending(true)
    setError('')
    try {
      await sessionApi.resendVerification({ email })
      setResendCooldown(60)
      setCode(EMPTY)
      inputRefs.current[0]?.focus()
    } catch (err) {
      setError(messageOf(err, 'Не удалось отправить код ещё раз'))
    } finally {
      setIsResending(false)
    }
  }

  return createPortal(
    <div className="verify">
      <div className="verify__card" role="dialog" aria-modal="true" aria-labelledby="verify-title">
        <div className="verify__bar">
          <span className="verify__glyph" aria-hidden="true">
            {'{'}
            <span>@</span>
            {'}'}
          </span>
          <button type="button" className="verify__close" onClick={onClose} aria-label="Закрыть">
            ×
          </button>
        </div>
        <div className="verify__body">
          <div className="verify__header">
            <div className="verify__mark" aria-hidden="true">
              <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5">
                <path
                  strokeLinecap="round"
                  strokeLinejoin="round"
                  d="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
                />
              </svg>
            </div>
            <h2 id="verify-title" className="verify__title">
              Подтвердите почту
            </h2>
            <p className="verify__subtitle">
              Мы отправили 6-значный код на
              <br />
              <strong>{maskEmail(email)}</strong>
            </p>
            <p className="verify__hint">
              Не видите письмо? Проверьте папку «Спам» — иногда код попадает туда.
            </p>
          </div>

          {error && (
            <div className="verify__error" role="alert">
              <span>{error}</span>
            </div>
          )}

          <div className="verify__form" onPaste={handlePaste}>
            <div className="verify__inputs">
              {SLOTS.map((slot) => (
                <input
                  key={slot}
                  ref={(element) => {
                    inputRefs.current[slot] = element
                  }}
                  type="text"
                  inputMode="numeric"
                  autoComplete={slot === 0 ? 'one-time-code' : 'off'}
                  maxLength={1}
                  value={code[slot] ?? ''}
                  aria-label={`Цифра ${slot + 1}`}
                  disabled={isLoading}
                  className={error ? 'verify__input is-error' : 'verify__input'}
                  onChange={(event) => handleInputChange(slot, event.target.value)}
                  onKeyDown={(event) => handleKeyDown(slot, event)}
                />
              ))}
            </div>
            <button
              type="button"
              className="verify__submit"
              disabled={isLoading || code.some((digit) => digit === '')}
              onClick={() => void handleVerify(code.join(''))}
            >
              {isLoading ? 'Проверяем…' : 'Подтвердить аккаунт'}
            </button>
          </div>

          <p className="verify__footer">
            Не пришёл код?
            <button
              type="button"
              className="verify__resend"
              disabled={isResending || resendCooldown > 0}
              onClick={() => void handleResend()}
            >
              {resendCooldown > 0
                ? `Повторно через ${resendCooldown} с`
                : isResending
                  ? 'Отправка…'
                  : 'Отправить снова'}
            </button>
          </p>
        </div>
      </div>
    </div>,
    document.body,
  )
}
