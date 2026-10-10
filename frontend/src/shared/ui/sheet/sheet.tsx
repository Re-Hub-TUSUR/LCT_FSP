import { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Ornament } from '../ornament/ornament'
import './sheet.css'

const FOCUSABLE =
  'a[href], button:not([disabled]), input:not([disabled]), select:not([disabled]), textarea:not([disabled]), [tabindex]:not([tabindex="-1"])'

type Props = {
  /** Short name in the bar: «Кандидат», «Вакансия». */
  label: string
  /** Id of the heading inside the sheet that names the dialog. Defaults to the bar label. */
  labelledBy?: string
  onClose: () => void
  children: ReactNode
  /** Actions pinned under the scrolling body. */
  footer?: ReactNode
  size?: 'default' | 'wide'
}

/**
 * Side sheet on the right: slides in over a scrim, the body scrolls, the footer stays.
 * Closes on Esc, on the scrim and on «Закрыть»; leaving is animated unless motion is reduced.
 */
export function Sheet({ label, labelledBy, onClose, children, footer, size = 'default' }: Props) {
  const labelId = useId()
  const closeRef = useRef<HTMLButtonElement>(null)
  const sheetRef = useRef<HTMLElement>(null)
  const [leaving, setLeaving] = useState(false)

  const requestClose = useCallback(() => {
    if (leaving) return
    if (window.matchMedia?.('(prefers-reduced-motion: reduce)').matches) {
      onClose()
      return
    }
    setLeaving(true)
  }, [leaving, onClose])

  useEffect(() => {
    closeRef.current?.focus()
  }, [])

  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (event.key !== 'Escape') return
      // A modal opened from the sheet closes first.
      if (document.querySelector('dialog[open]')) return
      requestClose()
    }
    document.addEventListener('keydown', onKey)
    return () => document.removeEventListener('keydown', onKey)
  }, [requestClose])

  // The page under the scrim is out of reach for the pointer; Tab stays in the sheet as well.
  useEffect(() => {
    const onTab = (event: KeyboardEvent) => {
      const sheet = sheetRef.current
      if (event.key !== 'Tab' || !sheet || document.querySelector('dialog[open]')) return
      // Only what is on screen: a hidden file input would take the focus nowhere.
      const items = [...sheet.querySelectorAll<HTMLElement>(FOCUSABLE)].filter(
        (item) => item.getClientRects().length > 0,
      )
      const first = items[0]
      const last = items[items.length - 1]
      if (!first || !last) return
      const active = document.activeElement
      if (!sheet.contains(active)) {
        event.preventDefault()
        first.focus()
      } else if (event.shiftKey && active === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && active === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onTab)
    return () => document.removeEventListener('keydown', onTab)
  }, [])

  // The animation end is the normal way out; the timer covers browsers that skip it.
  useEffect(() => {
    if (!leaving) return
    const timer = window.setTimeout(onClose, 500)
    return () => window.clearTimeout(timer)
  }, [leaving, onClose])

  const state = leaving ? ' is-leaving' : ''

  return (
    <>
      <div className={`sheet__scrim${state}`} aria-hidden="true" onClick={requestClose} />
      <aside
        ref={sheetRef}
        className={`sheet${size === 'wide' ? ' sheet--wide' : ''}${state}`}
        role="dialog"
        aria-modal="true"
        aria-labelledby={labelledBy ?? labelId}
        onAnimationEnd={(event) => {
          if (event.target === event.currentTarget && leaving) onClose()
        }}
      >
        <header className="sheet__bar">
          <p id={labelId} className="sheet__label">
            {label}
          </p>
          <button ref={closeRef} type="button" className="sheet__close" onClick={requestClose}>
            Закрыть
          </button>
        </header>
        <Ornament className="sheet__ornament" />
        <div className="sheet__body">{children}</div>
        {footer && <footer className="sheet__foot">{footer}</footer>}
      </aside>
    </>
  )
}

/** Titled block inside a sheet: «Стек», «О себе». */
export function SheetSection({ title, children }: { title: string; children: ReactNode }) {
  return (
    <section className="sheet-section" aria-label={title}>
      <p className="sheet-section__title">{title}</p>
      {children}
    </section>
  )
}
