import { useId } from 'react'
import type { ReactNode } from 'react'
import './panel.css'

type PanelProps = {
  title: string
  /** Link or button on the right of the title. */
  action?: ReactNode
  children?: ReactNode
  className?: string
}

export function Panel({ title, action, children, className }: PanelProps) {
  const titleId = useId()
  return (
    <section className={className ? `panel ${className}` : 'panel'} aria-labelledby={titleId}>
      <header className="panel__head">
        <h2 id={titleId} className="panel__title">
          {title}
        </h2>
        {action && <div className="panel__action">{action}</div>}
      </header>
      {children}
    </section>
  )
}

export type DataRow = {
  key: string
  label: string
  value: ReactNode
  /** Shown under the value in the dim colour. */
  note?: ReactNode
}

/** Read view of a profile block: label, value, optional note. Empty values say so. */
export function DataRows({ rows }: { rows: DataRow[] }) {
  return (
    <dl className="data-rows">
      {rows.map((row) => (
        <div key={row.key} className="data-rows__row">
          <dt className="data-rows__label">{row.label}</dt>
          <dd className="data-rows__value">
            {isEmpty(row.value) ? <span className="data-rows__empty">Не указано</span> : row.value}
            {row.note && <span className="data-rows__note">{row.note}</span>}
          </dd>
        </div>
      ))}
    </dl>
  )
}

function isEmpty(value: ReactNode): boolean {
  if (value === null || value === undefined || value === false) return true
  if (typeof value === 'string') return value.trim() === ''
  if (Array.isArray(value)) return value.length === 0
  return false
}

export type StatusTone = 'done' | 'wait' | 'todo' | 'new' | 'off'

export function StatusTag({ tone, children }: { tone: StatusTone; children: ReactNode }) {
  return <span className={`status-tag status-tag--${tone}`}>{children}</span>
}

/** Mono chips for skills and short facts. */
export function ChipList({ items, label }: { items: string[]; label?: string }) {
  return (
    <ul className="chip-list" aria-label={label}>
      {items.map((item) => (
        <li key={item}>{item}</li>
      ))}
    </ul>
  )
}
