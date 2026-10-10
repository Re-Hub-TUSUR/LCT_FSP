import { useEffect, useRef } from 'react'
import type { ReactNode } from 'react'
import './tabs.css'

export type TabItem<T extends string> = {
  value: T
  label: ReactNode
  /** Number next to the label; hidden while unknown. */
  count?: number | null
  /** Colour of the number: mutual interest is light blue, skipped is red. */
  tone?: 'accent' | 'danger'
  /** Red badge instead of a plain number, e.g. unread messages. */
  badge?: boolean
}

type TabsProps<T extends string> = {
  items: readonly TabItem<T>[]
  value: T
  onChange: (value: T) => void
  label: string
  className?: string
}

/** Underlined tabs with counters. Buttons with `aria-pressed`: they switch a view, not panels. */
export function Tabs<T extends string>({ items, value, onChange, label, className }: TabsProps<T>) {
  const ref = useRef<HTMLElement>(null)

  // On a phone the row scrolls sideways: the open tab must not stay behind its edge.
  useEffect(() => {
    const row = ref.current
    const tab = row?.querySelector<HTMLElement>(`[data-tab="${value}"]`)
    if (!row || !tab) return
    const box = row.getBoundingClientRect()
    const own = tab.getBoundingClientRect()
    if (own.left < box.left) row.scrollLeft += own.left - box.left
    else if (own.right > box.right) row.scrollLeft += own.right - box.right
  }, [value])

  return (
    <nav ref={ref} className={className ? `tabs ${className}` : 'tabs'} aria-label={label}>
      {items.map((item) => (
        <button
          key={item.value}
          type="button"
          data-tab={item.value}
          className={item.value === value ? 'tabs__tab is-active' : 'tabs__tab'}
          aria-pressed={item.value === value}
          onClick={() => onChange(item.value)}
        >
          {item.label}
          {item.count !== undefined && item.count !== null && (!item.badge || item.count > 0) && (
            <span
              className={
                item.badge
                  ? 'tabs__badge'
                  : item.tone
                    ? `tabs__count tabs__count--${item.tone}`
                    : 'tabs__count'
              }
            >
              {item.count}
            </span>
          )}
        </button>
      ))}
    </nav>
  )
}

type SegmentedProps<T extends string> = {
  items: readonly { value: T; label: string }[]
  value: T
  onChange: (value: T) => void
  label: string
  className?: string
}

/** Segmented switch on a filled ground: the chosen segment is blue. */
export function Segmented<T extends string>({
  items,
  value,
  onChange,
  label,
  className,
}: SegmentedProps<T>) {
  return (
    <div
      className={className ? `segmented ${className}` : 'segmented'}
      role="group"
      aria-label={label}
    >
      {items.map((item) => (
        <button
          key={item.value}
          type="button"
          className={item.value === value ? 'segmented__item is-active' : 'segmented__item'}
          aria-pressed={item.value === value}
          onClick={() => onChange(item.value)}
        >
          {item.label}
        </button>
      ))}
    </div>
  )
}
