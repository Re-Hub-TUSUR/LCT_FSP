import type { ReactNode } from 'react'
import { Button } from '../button/button'
import './feedback.css'

/** The ФСП sign «[•]» of empty states and loaders; the dot blinks while something loads. */
export function FspMark({ pulse = false }: { pulse?: boolean }) {
  return (
    <span className={pulse ? 'fsp-mark fsp-mark--pulse' : 'fsp-mark'} aria-hidden="true">
      [<span className="fsp-mark__dot">•</span>]
    </span>
  )
}

export function Loader({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="feedback feedback--loading" role="status" aria-live="polite">
      <FspMark pulse />
      <span className="feedback__text">{label}</span>
    </div>
  )
}

type ErrorStateProps = {
  title?: string
  message: string
  onRetry?: () => void
}

export function ErrorState({
  title = 'Не удалось загрузить данные',
  message,
  onRetry,
}: ErrorStateProps) {
  return (
    <div className="feedback feedback--error" role="alert">
      <p className="feedback__title">{title}</p>
      <p className="feedback__text">{message}</p>
      {onRetry && (
        <Button variant="ghost" size="inline" onClick={onRetry}>
          Повторить
        </Button>
      )}
    </div>
  )
}

export function EmptyState({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <div className="feedback">
      <FspMark />
      <p className="feedback__title">{title}</p>
      {children && <div className="feedback__text">{children}</div>}
    </div>
  )
}
