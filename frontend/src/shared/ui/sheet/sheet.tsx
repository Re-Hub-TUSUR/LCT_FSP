import { useCallback, useEffect, useId, useRef, useState } from 'react'
import type { ReactNode } from 'react'
import { Ornament } from '../ornament/ornament'
import './sheet.css'

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
