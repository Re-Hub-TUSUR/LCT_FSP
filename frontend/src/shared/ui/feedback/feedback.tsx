import type { ReactNode } from 'react'
import { Button } from '../button/button'
import './feedback.css'

export function Loader({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="feedback" role="status" aria-live="polite">
      <span className="feedback__spinner" aria-hidden="true" />
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
      <p className="feedback__title">{title}</p>
      {children && <div className="feedback__text">{children}</div>}
    </div>
  )
}
