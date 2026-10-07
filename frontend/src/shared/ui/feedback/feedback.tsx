import type { ReactNode } from 'react'
import { Button } from '../button/button'
import './feedback.css'

const HOLE_ROWS = [6.4, 11.15, 15.9, 20.65]

/** The film-frame mark of the logo with its sprocket holes lit in turn, as on the splash in index.html. */
function FilmMark() {
  return (
    <svg className="feedback__mark" viewBox="0 0 32 32" aria-hidden="true">
      <path
        fill="currentColor"
        fillRule="evenodd"
        d="M7,3H25A3,3 0 0 1 28,6V26A3,3 0 0 1 25,29H7A3,3 0 0 1 4,26V6A3,3 0 0 1 7,3ZM11.7,7.6H20.3A0.4,0.4 0 0 1 20.7,8V24A0.4,0.4 0 0 1 20.3,24.4H11.7A0.4,0.4 0 0 1 11.3,24V8A0.4,0.4 0 0 1 11.7,7.6Z"
      />
      {[6.15, 23.15].map((x) =>
        HOLE_ROWS.map((y, row) => (
          <rect
            key={`${x}-${y}`}
            className="feedback__hole"
            style={{ animationDelay: `${row * 0.16}s` }}
            x={x}
            y={y}
            width="2.7"
            height="3.15"
            rx="0.55"
          />
        )),
      )}
    </svg>
  )
}

export function Loader({ label = 'Загрузка…' }: { label?: string }) {
  return (
    <div className="feedback feedback--loading" role="status" aria-live="polite">
      <FilmMark />
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
