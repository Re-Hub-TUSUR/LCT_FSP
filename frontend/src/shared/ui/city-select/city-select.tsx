import { useEffect, useId, useRef, useState } from 'react'
import type { KeyboardEvent } from 'react'
import { http } from '@/shared/api'
import './city-select.css'

export type CityOption = {
  id: number
  name: string
  countryCode: string
  region: string | null
  latitude: number
  longitude: number
}

const DEBOUNCE_MS = 300
const MIN_QUERY = 2

export async function searchCities(query: string, signal?: AbortSignal): Promise<CityOption[]> {
  return http.get<CityOption[]>('/cities/search', {
    query: { q: query, countryCode: 'RU', limit: 10 },
    signal,
  })
}

/** «Киров, Кировская область» when the list has another place with the same name. */
export function cityOptionLabel(city: CityOption, options: readonly CityOption[]): string {
  const namesakes = options.filter((item) => item.name === city.name)
  if (namesakes.length > 1 && city.region) return `${city.name}, ${city.region}`
  return city.name
}

type Props = {
  id: string
  label: string
  /** Canonical name of the selected place. Empty until the person picks one. */
  name: string
  error?: string
  /** Text recognised in a file: shown under the field, never saved as the city. */
  hint?: string
  onPick: (city: CityOption) => void
  onClear: () => void
}

/** A city from the directory. Typing searches; only a picked row is a value. */
export function CitySelect({ id, label, name, error, hint, onPick, onClear }: Props) {
  const listId = useId()
  const root = useRef<HTMLDivElement>(null)
  const [text, setText] = useState(name)
  const [seenName, setSeenName] = useState(name)
  const [open, setOpen] = useState(false)
  const [options, setOptions] = useState<CityOption[]>([])
  const [active, setActive] = useState(0)
  const [busy, setBusy] = useState(false)

  // A new saved city replaces whatever was typed. Done here so the field does not lag a frame.
  if (name !== seenName) {
    setSeenName(name)
    setText(name)
  }

  const query = (name === seenName ? text : name).trim()
  const canSearch = open && query.length >= MIN_QUERY && query !== name
  if (!canSearch && (options.length > 0 || busy)) {
    setOptions([])
    setBusy(false)
  }

  useEffect(() => {
    if (!canSearch) return
    const controller = new AbortController()
    const timer = window.setTimeout(() => {
      setBusy(true)
      searchCities(query, controller.signal)
        .then((rows) => {
          setOptions(rows)
          setActive(0)
        })
        .catch((reason: unknown) => {
          if (!controller.signal.aborted) setOptions([])
          void reason
        })
        .finally(() => {
          if (!controller.signal.aborted) setBusy(false)
        })
    }, DEBOUNCE_MS)
    return () => {
      window.clearTimeout(timer)
      controller.abort()
    }
  }, [canSearch, query])

  useEffect(() => {
    const close = (event: PointerEvent) => {
      if (!root.current?.contains(event.target as Node)) setOpen(false)
    }
    document.addEventListener('pointerdown', close)
    return () => document.removeEventListener('pointerdown', close)
  }, [])

  const pick = (city: CityOption) => {
    setText(city.name)
    setOpen(false)
    setOptions([])
    onPick(city)
  }

  const onKeyDown = (event: KeyboardEvent<HTMLInputElement>) => {
    if (event.key === 'ArrowDown') {
      event.preventDefault()
      setOpen(true)
      setActive((index) => Math.min(index + 1, Math.max(options.length - 1, 0)))
    } else if (event.key === 'ArrowUp') {
      event.preventDefault()
      setActive((index) => Math.max(index - 1, 0))
    } else if (event.key === 'Enter' && open && options[active]) {
      event.preventDefault()
      const city = options[active]
      if (city) pick(city)
    } else if (event.key === 'Escape') {
      setOpen(false)
    }
  }

  const shown = open && (options.length > 0 || busy || text.trim().length >= MIN_QUERY)
  const activeId = options[active] ? `${listId}-${options[active].id}` : undefined

  return (
    <div className="field city-select" ref={root}>
      <label className="field__label" htmlFor={id}>
        {label}
      </label>
      <div className="city-select__control">
        <input
          id={id}
          className="field__input"
          role="combobox"
          aria-expanded={open}
          aria-controls={listId}
          aria-autocomplete="list"
          aria-activedescendant={open ? activeId : undefined}
          aria-invalid={error ? true : undefined}
          aria-describedby={error ? `${id}-error` : hint ? `${id}-hint` : undefined}
          autoComplete="off"
          value={text}
          onChange={(event) => {
            setText(event.target.value)
            setOpen(true)
            if (name) onClear()
          }}
          onFocus={() => setOpen(true)}
          onKeyDown={onKeyDown}
        />
        {shown && (
          <div className="city-select__list" id={listId} role="listbox">
            {options.length === 0 ? (
              <div className="city-select__empty">
                {busy ? 'Ищем…' : 'Нет такого населённого пункта'}
              </div>
            ) : (
              options.map((city, index) => (
                <div
                  key={city.id}
                  id={`${listId}-${city.id}`}
                  role="option"
                  tabIndex={-1}
                  aria-selected={index === active}
                  className={
                    index === active ? 'city-select__option is-active' : 'city-select__option'
                  }
                  onMouseEnter={() => setActive(index)}
                  onMouseDown={(event) => {
                    event.preventDefault()
                    pick(city)
                  }}
                >
                  {cityOptionLabel(city, options)}
                </div>
              ))
            )}
          </div>
        )}
      </div>
      <p id={`${id}-error`} className="field__error" role="alert">
        {error}
      </p>
      {hint ? (
        <p id={`${id}-hint`} className="city-select__hint">
          В файле: {hint}. Выберите город из списка.
        </p>
      ) : null}
    </div>
  )
}
