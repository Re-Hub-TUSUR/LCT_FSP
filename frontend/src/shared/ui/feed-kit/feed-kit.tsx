import type { ButtonHTMLAttributes, ReactNode } from 'react'
import './feed-kit.css'
import './match-card.css'
import './feed-layout.css'

/** Toggle chip for filters: pressed state is announced to screen readers. */
export function Chip({
  active,
  className,
  ...rest
}: ButtonHTMLAttributes<HTMLButtonElement> & { active?: boolean }) {
  return (
    <button
      type="button"
      aria-pressed={active}
      className={['chip-toggle', active && 'is-active', className].filter(Boolean).join(' ')}
      {...rest}
    />
  )
}

/** Horizontal meter for a 0..1 value: match to a vacancy, profile strength. */
export function MatchMeter({ value, label }: { value: number; label: string }) {
  const percent = Math.round(Math.max(0, Math.min(1, value)) * 100)
  const tone = percent >= 75 ? 'high' : percent >= 50 ? 'mid' : 'low'
  return (
    <div className={`meter meter--${tone}`}>
      <div className="meter__head">
        <span className="meter__label">{label}</span>
        <span className="meter__value">{percent}%</span>
      </div>
      <div
        className="meter__track"
        role="meter"
        aria-label={label}
        aria-valuemin={0}
        aria-valuemax={100}
        aria-valuenow={percent}
      >
        <span className="meter__fill" style={{ width: `${percent}%` }} />
      </div>
    </div>
  )
}

const PAGE_SIZES = [10, 20, 50] as const

type PaginationProps = {
  page: number
  pages: number
  perPage: number
  total: number
  onPage: (page: number) => void
  onPerPage: (perPage: number) => void
}

/** Page numbers with gaps (1 … 4 5 6 … 12) and a page-size switch. */
export function Pagination({ page, pages, perPage, total, onPage, onPerPage }: PaginationProps) {
  // 1 … 4 5 6 … 12: the edges and the neighbours of the current page.
  const shown = Array.from({ length: pages }, (_, i) => i + 1).filter(
    (n) => n === 1 || n === pages || Math.abs(n - page) <= 1,
  )
  const items: (number | 'gap')[] = []
  shown.forEach((n, i) => {
    if (i > 0 && n - shown[i - 1]! > 1) items.push('gap')
    items.push(n)
  })

  return (
    <nav className="pager" aria-label="Страницы">
      <p className="pager__total">Найдено: {total}</p>
      {pages > 1 && (
        <div className="pager__pages">
          <button type="button" disabled={page <= 1} onClick={() => onPage(page - 1)}>
            ←<span className="visually-hidden">Предыдущая</span>
          </button>
          {items.map((item, i) =>
            item === 'gap' ? (
              <span key={`gap-${i}`} className="pager__gap">
                …
              </span>
            ) : (
              <button
                key={item}
                type="button"
                aria-current={item === page ? 'page' : undefined}
                className={item === page ? 'is-current' : undefined}
                onClick={() => onPage(item)}
              >
                {item}
              </button>
            ),
          )}
          <button type="button" disabled={page >= pages} onClick={() => onPage(page + 1)}>
            →<span className="visually-hidden">Следующая</span>
          </button>
        </div>
      )}
      <label className="pager__size">
        На странице
        <select value={perPage} onChange={(e) => onPerPage(Number(e.target.value))}>
          {PAGE_SIZES.map((size) => (
            <option key={size} value={size}>
              {size}
            </option>
          ))}
        </select>
      </label>
    </nav>
  )
}

/** Uppercase mono notice line, e.g. demo-data or engine hints. */
export function Notice({ children }: { children: ReactNode }) {
  return <p className="notice">{children}</p>
}

/** Card skeletons while a page of the feed loads. */
export function FeedSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="feed-skeleton" role="status" aria-label="Загрузка">
      {Array.from({ length: count }, (_, i) => (
        <div key={i} className="feed-skeleton__card" />
      ))}
    </div>
  )
}
