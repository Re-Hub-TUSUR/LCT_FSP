import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent, ReactNode } from 'react'
import { formatNumber } from '@/shared/lib'
import { Chip } from '../feed-kit/feed-kit'
import './filter-kit.css'

type FilterHeadProps = {
  /** Groups with a value: the badge next to the title. */
  active: number
  /** «Сбросить» or «Вернуть из вакансии»; hidden when there is nothing to undo. */
  resetLabel: string | null
  onReset: () => void
  /** «12 кандидатов из 120»; empty while counting. */
  count: ReactNode
}

/** Title of a filter panel with the active-filter badge, the reset link and the result count. */
export function FilterHead({ active, resetLabel, onReset, count }: FilterHeadProps) {
  return (
    <div className="filters-head">
      <div className="filters-head__row">
        <p className="filters-head__title">
          Фильтры
          {active > 0 && (
            <span className="filters-badge" aria-label={`, выбрано: ${active}`}>
              {active}
            </span>
          )}
        </p>
        {resetLabel && (
          <button type="button" className="filters-link" onClick={onReset}>
            {resetLabel}
          </button>
        )}
      </div>
      <p className="filters-head__count" aria-live="polite">
        {count}
      </p>
    </div>
  )
}

type FilterGroupProps = {
  label: string
  /** Right side of the label: a hint («для офиса и гибрида») or where the value came from. */
  aside?: ReactNode
  children: ReactNode
}

export function FilterGroup({ label, aside, children }: FilterGroupProps) {
  const id = useId()
  return (
    <div className="filters-group" role="group" aria-labelledby={id}>
      <div className="filters-group__label">
        <span id={id}>{label}</span>
        {aside && <span className="filters-group__aside">{aside}</span>}
      </div>
      {children}
    </div>
  )
}

/** «Обязательно — отсекает остальных» inside a group. */
export function FilterSubLabel({ children, hint }: { children: ReactNode; hint?: string }) {
  return (
    <p className="filters-sub">
      {children}
      {hint && <span>{hint}</span>}
    </p>
  )
}

/** A value filled in from a vacancy or a profile: as it came, or changed with a way back. */
export type MarkState = 'source' | 'changed' | null

export function SourceMark({
  state,
  source,
  onRevert,
}: {
  state: MarkState
  /** «из вакансии», «из профиля». */
  source: string
  onRevert: () => void
}) {
  if (state === 'source') return <span className="filters-mark">{source}</span>
  if (state === 'changed')
    return (
      <span className="filters-mark">
        изменено
        <button type="button" onClick={onRevert}>
          вернуть
        </button>
      </span>
    )
  return null
}

type CountChipProps = {
  active: boolean
  onClick: () => void
  children: ReactNode
  /** A count or a gain («+3»); nothing while unknown. */
  count?: number | string | null
  /** Nothing behind the option: drawn dashed. */
  empty?: boolean
}

/** A filter chip with the number of results the option leaves. */
export function CountChip({ active, onClick, children, count, empty }: CountChipProps) {
  return (
    <Chip active={active} onClick={onClick} className={empty && !active ? 'is-empty' : undefined}>
      {children}
      {count !== undefined && count !== null && count !== '' && (
        <>
          {' '}
          <span className="chip-toggle__count">{count}</span>
        </>
      )}
    </Chip>
  )
}

type CheckRowProps = {
  checked: boolean
  onChange: (checked: boolean) => void
  children: ReactNode
  count?: number | null
}

export function CheckRow({ checked, onChange, children, count }: CheckRowProps) {
  return (
    <label className="filters-check">
      <input type="checkbox" checked={checked} onChange={(e) => onChange(e.target.checked)} />
      <span className="filters-check__text">{children}</span>
      {count !== undefined && count !== null && (
        <>
          {' '}
          <span className="filters-check__count">{count}</span>
        </>
      )}
    </label>
  )
}

const MONEY_DIGITS = 7
const COMMIT_DELAY = 500

function digitsOf(text: string): number | null {
  const digits = text.replace(/\D/g, '').replace(/^0+/, '').slice(0, MONEY_DIGITS)
  return digits ? Number(digits) : null
}

type MoneyFieldProps = {
  label: string
  /** «от», «до» before the number. */
  prefix?: string
  value: number | null
  placeholder?: string
  onChange: (value: number | null) => void
}

/** Rubles typed with thousands separated; the value is applied after a short pause or on blur. */
export function MoneyField({ label, prefix, value, placeholder, onChange }: MoneyFieldProps) {
  // While typing the field shows its own text; otherwise it follows the value (a reset, a preset).
  const [draft, setDraft] = useState<string | null>(null)
  const timer = useRef<number | undefined>(undefined)
  // The delayed commit must see the filters as they are then, not as they were when typing.
  const latest = useRef({ value, onChange })
  useEffect(() => {
    latest.current = { value, onChange }
  })
  useEffect(() => () => window.clearTimeout(timer.current), [])

  const commit = (text: string) => {
    window.clearTimeout(timer.current)
    const next = digitsOf(text)
    if (next !== latest.current.value) latest.current.onChange(next)
  }

  return (
    <label className="filters-money">
      {prefix && <span className="filters-money__prefix">{prefix}</span>}
      <input
        inputMode="numeric"
        aria-label={label}
        placeholder={placeholder}
        value={draft ?? (value ? formatNumber(value) : '')}
        onChange={(e) => {
          const next = digitsOf(e.target.value)
          const text = next === null ? '' : formatNumber(next)
          setDraft(text)
          window.clearTimeout(timer.current)
          timer.current = window.setTimeout(() => commit(text), COMMIT_DELAY)
        }}
        onBlur={() => {
          if (draft !== null) commit(draft)
          setDraft(null)
        }}
        onKeyDown={(e) => {
          if (e.key === 'Enter' && draft !== null) commit(draft)
        }}
      />
    </label>
  )
}

export type ComboOption = {
  value: string
  label: string
  count?: number
  /** Why the option is offered, e.g. «по запросу «питон»». */
  hint?: string
}

type TagComboboxProps = {
  label: string
  placeholder: string
  values: readonly string[]
  tagLabel?: (value: string) => string
  /** Options for the typed text, the chosen values left out. */
  options: (query: string) => ComboOption[]
  onAdd: (values: string[]) => void
  onRemove: (value: string) => void
  /** Typed or pasted text («Python, Kafka»): what each comma-separated part stands for. */
  resolve?: (text: string) => string | null
  /** A button on every tag that moves it to the other list. */
  move?: { symbol: string; title: string; onMove: (value: string) => void }
  /** Dashed tags: «Будет плюсом». */
  soft?: boolean
  emptyText: string
}

/** Several values picked from suggestions with counts; tags can be removed or moved. */
export function TagCombobox({
  label,
  placeholder,
  values,
  tagLabel = (value) => value,
  options,
  onAdd,
  onRemove,
  resolve,
  move,
  soft,
  emptyText,
}: TagComboboxProps) {
  const [query, setQuery] = useState('')
  const [open, setOpen] = useState(false)
  const [active, setActive] = useState(0)
  const input = useRef<HTMLInputElement>(null)
  const listId = useId()
  const items = open ? options(query.trim()) : []
  const current = Math.min(active, Math.max(0, items.length - 1))

  const add = (value: string) => {
    onAdd([value])
    setQuery('')
    setActive(0)
  }

  const type = (text: string) => {
    if (resolve && text.includes(',')) {
      const parts = text.split(',')
      const rest = parts.pop() ?? ''
      const found = parts.map((part) => resolve(part.trim())).filter((v): v is string => !!v)
      if (found.length) onAdd([...new Set(found)])
      setQuery(rest.trimStart())
    } else {
      setQuery(text)
    }
    setActive(0)
    setOpen(true)
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setOpen(true)
      setActive(Math.min(items.length - 1, current + 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive(Math.max(0, current - 1))
    } else if (e.key === 'Enter') {
      const item = items[current]
      if (item) {
        e.preventDefault()
        add(item.value)
      }
    } else if (e.key === 'Escape') {
      setOpen(false)
    } else if (e.key === 'Backspace' && !query && values.length) {
      onRemove(values[values.length - 1]!)
    }
  }

  return (
    <div className={['filters-combo', open && 'is-open'].filter(Boolean).join(' ')}>
      {/* A click on the empty part of the field focuses the input, as in a text field. */}
      {/* oxlint-disable-next-line jsx-a11y/no-static-element-interactions */}
      <div
        className="filters-combo__field"
        onMouseDown={(e) => {
          if (e.target === e.currentTarget) {
            e.preventDefault()
            input.current?.focus()
          }
        }}
      >
        {values.map((value) => (
          <span
            key={value}
            className={['filters-tag', soft && 'is-soft'].filter(Boolean).join(' ')}
          >
            {tagLabel(value)}
            {move && (
              <button
                type="button"
                className="filters-tag__move"
                title={move.title}
                aria-label={`${move.title}: ${tagLabel(value)}`}
                onClick={() => move.onMove(value)}
              >
                {move.symbol}
              </button>
            )}
            <button
              type="button"
              aria-label={`Убрать ${tagLabel(value)}`}
              onClick={() => onRemove(value)}
            >
              ×
            </button>
          </span>
        ))}
        <input
          ref={input}
          role="combobox"
          aria-label={label}
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open && items[current] ? `${listId}-${current}` : undefined}
          placeholder={values.length ? 'Добавить' : placeholder}
          value={query}
          onChange={(e) => type(e.target.value)}
          onFocus={() => setOpen(true)}
          onBlur={() => setOpen(false)}
          onKeyDown={onKeyDown}
        />
      </div>
      {open && (
        <div className="filters-combo__list" id={listId} role="listbox" aria-label={label}>
          {items.length ? (
            items.map((item, index) => (
              <div
                key={item.value}
                id={`${listId}-${index}`}
                role="option"
                tabIndex={-1}
                aria-selected={index === current}
                className={index === current ? 'is-active' : undefined}
                onMouseDown={(e) => {
                  e.preventDefault()
                  add(item.value)
                }}
              >
                <span>
                  {item.label}
                  {item.hint && <small>{item.hint}</small>}
                </span>
                {item.count !== undefined && (
                  <span className="filters-combo__count">{item.count}</span>
                )}
              </div>
            ))
          ) : (
            <div className="filters-combo__none" role="presentation">
              {emptyText}
            </div>
          )}
        </div>
      )}
    </div>
  )
}

export type ModeOption = {
  id: string
  title: string
  subtitle: string
  /** «12 подходят», «94 всего». */
  note?: string
  /** A header shown before the first option of a section («Мои вакансии»). */
  section?: string
}

type ModeSelectProps = {
  label: string
  options: ModeOption[]
  value: string
  onChange: (id: string) => void
  searchPlaceholder: string
  emptyText: string
  /** Drawn with an accent edge: the panel works for a vacancy, not the free search. */
  accented?: boolean
}

/** What the filters start from: a dropdown with a search over the options. */
export function ModeSelect({
  label,
  options,
  value,
  onChange,
  searchPlaceholder,
  emptyText,
  accented,
}: ModeSelectProps) {
  const [open, setOpen] = useState(false)
  const [query, setQuery] = useState('')
  const [active, setActive] = useState(0)
  const root = useRef<HTMLDivElement>(null)
  const button = useRef<HTMLButtonElement>(null)
  const listId = useId()
  const current = options.find((option) => option.id === value) ?? options[0]
  const needle = query.trim().toLowerCase()
  const shown = options.filter(
    (option) => !needle || `${option.title} ${option.subtitle}`.toLowerCase().includes(needle),
  )
  const focused = Math.min(active, Math.max(0, shown.length - 1))

  useEffect(() => {
    if (!open) return
    const close = (e: MouseEvent) => {
      if (!root.current?.contains(e.target as Node)) setOpen(false)
    }
    document.addEventListener('mousedown', close)
    return () => document.removeEventListener('mousedown', close)
  }, [open])

  const pick = (id: string) => {
    setOpen(false)
    button.current?.focus()
    if (id !== value) onChange(id)
  }

  const onKeyDown = (e: KeyboardEvent<HTMLInputElement>) => {
    if (e.key === 'ArrowDown') {
      e.preventDefault()
      setActive(Math.min(shown.length - 1, focused + 1))
    } else if (e.key === 'ArrowUp') {
      e.preventDefault()
      setActive(Math.max(0, focused - 1))
    } else if (e.key === 'Enter') {
      const option = shown[focused]
      if (option) pick(option.id)
    } else if (e.key === 'Escape') {
      setOpen(false)
      button.current?.focus()
    }
  }

  return (
    <div
      ref={root}
      className={['filters-mode', open && 'is-open', accented && 'is-accented']
        .filter(Boolean)
        .join(' ')}
    >
      <button
        ref={button}
        type="button"
        className="filters-mode__button"
        aria-haspopup="listbox"
        aria-expanded={open}
        aria-label={`${label}: ${current?.title ?? ''}`}
        onClick={() => {
          setQuery('')
          setActive(0)
          setOpen(!open)
        }}
      >
        <span>
          <span className="filters-mode__title">{current?.title}</span>
          <span className="filters-mode__subtitle">{current?.subtitle}</span>
        </span>
        <span className="filters-mode__caret" aria-hidden="true">
          ▼
        </span>
      </button>
      {open && (
        <div className="filters-mode__menu">
          <input
            className="filters-mode__search"
            role="combobox"
            aria-label={searchPlaceholder}
            aria-expanded="true"
            aria-controls={listId}
            aria-activedescendant={shown[focused] ? `${listId}-${focused}` : undefined}
            placeholder={searchPlaceholder}
            value={query}
            // The menu opens to search right away.
            // oxlint-disable-next-line jsx-a11y/no-autofocus
            autoFocus
            onChange={(e) => {
              setQuery(e.target.value)
              setActive(0)
            }}
            onKeyDown={onKeyDown}
          />
          <div className="filters-mode__list" id={listId} role="listbox" aria-label={label}>
            {shown.length === 0 && (
              <div className="filters-mode__empty" role="presentation">
                {emptyText}
              </div>
            )}
            {shown.map((option, index) => (
              <ModeItem
                key={option.id}
                id={`${listId}-${index}`}
                option={option}
                header={option.section !== shown[index - 1]?.section ? option.section : undefined}
                selected={option.id === value}
                focused={index === focused}
                onPick={() => pick(option.id)}
              />
            ))}
          </div>
        </div>
      )}
    </div>
  )
}

function ModeItem({
  id,
  option,
  header,
  selected,
  focused,
  onPick,
}: {
  id: string
  option: ModeOption
  header?: string
  selected: boolean
  focused: boolean
  onPick: () => void
}) {
  return (
    <>
      {header && (
        <div className="filters-mode__section" role="presentation">
          {header}
        </div>
      )}
      <div
        id={id}
        role="option"
        tabIndex={-1}
        aria-selected={selected}
        className={['filters-mode__option', selected && 'is-selected', focused && 'is-active']
          .filter(Boolean)
          .join(' ')}
        onMouseDown={(e) => {
          e.preventDefault()
          onPick()
        }}
      >
        <span className="filters-mode__body">
          <span className="filters-mode__title">{option.title}</span>
          <span className="filters-mode__subtitle">{option.subtitle}</span>
        </span>
        {option.note && <span className="filters-mode__note">{option.note}</span>}
      </div>
    </>
  )
}

export type Relaxation = {
  key: string
  label: string
  /** Results the change brings back. */
  gain: number
  apply: () => void
}

/** Nothing matched: the filters worth loosening, the most rewarding first. */
export function FilterDeadEnd({
  title,
  relaxations,
  fallback,
}: {
  title: string
  relaxations: Relaxation[]
  /** When no single change helps: back to the preset or no filters at all. */
  fallback: Relaxation
}) {
  return (
    <div className="filters-dead-end" role="status">
      <p className="filters-dead-end__title">{title}</p>
      <p className="filters-dead-end__text">
        {relaxations.length ? 'Ослабьте один из фильтров:' : 'Слишком много условий сразу.'}
      </p>
      {(relaxations.length ? relaxations : [fallback]).map((item) => (
        <button key={item.key} type="button" className="filters-relax" onClick={item.apply}>
          {item.label}
          <span>+{item.gain}</span>
        </button>
      ))}
    </div>
  )
}

/** Collapsible group of rarely used filters with the number of chosen ones. */
export function FilterDisclosure({
  title,
  chosen,
  children,
}: {
  title: string
  chosen: number
  children: ReactNode
}) {
  const [open, setOpen] = useState(chosen > 0)
  const id = useId()
  return (
    <div className="filters-disclosure">
      <button
        type="button"
        className="filters-disclosure__button"
        aria-expanded={open}
        aria-controls={id}
        onClick={() => setOpen(!open)}
      >
        {title}
        <span>
          {chosen > 0 && <span className="filters-badge">{chosen}</span>}
          <span className="filters-disclosure__arrow" aria-hidden="true">
            ›
          </span>
        </span>
      </button>
      <div id={id} className="filters-disclosure__body" hidden={!open}>
        {children}
      </div>
    </div>
  )
}

const TOAST_TIME = 5000

export type ToastState = { message: string; undo?: () => void } | null

/** «Фильтры заполнены из вакансии · Вернуть»: a short notice with an undo. */
export function UndoToast({ toast, onClose }: { toast: ToastState; onClose: () => void }) {
  useEffect(() => {
    if (!toast) return
    const timer = window.setTimeout(onClose, TOAST_TIME)
    return () => window.clearTimeout(timer)
  }, [toast, onClose])

  if (!toast) return null
  return (
    <div className="filters-toast" role="status">
      <span>{toast.message}</span>
      {toast.undo && (
        <button
          type="button"
          onClick={() => {
            toast.undo?.()
            onClose()
          }}
        >
          Вернуть
        </button>
      )}
    </div>
  )
}
