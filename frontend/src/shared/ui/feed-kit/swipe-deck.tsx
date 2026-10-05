import { useEffect, useRef, useState } from 'react'
import type { PointerEvent, ReactNode } from 'react'
import './feed-kit.css'

export type SwipeDecision = 'like' | 'skip'

type Props<T> = {
  items: T[]
  getKey: (item: T) => string
  renderCard: (item: T) => ReactNode
  onDecide: (item: T, decision: SwipeDecision) => void
  likeLabel: string
  skipLabel: string
  empty: ReactNode
}

const THRESHOLD = 110
const DRAG_START = 6

/**
 * Tinder-style deck: drag right to like, left to skip. Buttons and ←/→ keys are the
 * accessible path; the next card peeks behind the current one.
 */
export function SwipeDeck<T>({
  items,
  getKey,
  renderCard,
  onDecide,
  likeLabel,
  skipLabel,
  empty,
}: Props<T>) {
  const [offset, setOffset] = useState(0)
  const [leaving, setLeaving] = useState<SwipeDecision | null>(null)
  const start = useRef<number | null>(null)
  const current = items[0]
  const next = items[1]

  const decide = (decision: SwipeDecision) => {
    if (!current || leaving) return
    setLeaving(decision)
    window.setTimeout(() => {
      onDecide(current, decision)
      setLeaving(null)
      setOffset(0)
    }, 220)
  }

  const decideRef = useRef(decide)
  useEffect(() => {
    decideRef.current = decide
  })
  useEffect(() => {
    const onKey = (e: KeyboardEvent) => {
      if (e.target instanceof HTMLInputElement || e.target instanceof HTMLTextAreaElement) return
      if (e.key === 'ArrowRight') decideRef.current('like')
      if (e.key === 'ArrowLeft') decideRef.current('skip')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  if (!current) return <>{empty}</>

  const shift = leaving === 'like' ? 640 : leaving === 'skip' ? -640 : offset
  const hint = shift > 40 ? 'like' : shift < -40 ? 'skip' : null

  const bind = {
    onPointerDown: (e: PointerEvent<HTMLDivElement>) => {
      start.current = e.clientX
    },
    onPointerMove: (e: PointerEvent<HTMLDivElement>) => {
      if (start.current === null) return
      const dx = e.clientX - start.current
      if (Math.abs(dx) < DRAG_START) return
      if (!e.currentTarget.hasPointerCapture?.(e.pointerId)) {
        e.currentTarget.setPointerCapture?.(e.pointerId)
      }
      setOffset(dx)
    },
    onPointerUp: () => {
      start.current = null
      if (offset >= THRESHOLD) decide('like')
      else if (offset <= -THRESHOLD) decide('skip')
      else setOffset(0)
    },
    onPointerCancel: () => {
      start.current = null
      setOffset(0)
    },
  }

  return (
    <div className="swipe">
      <div className="swipe__stage">
        {next && (
          <div className="swipe__card swipe__card--next" aria-hidden="true">
            {renderCard(next)}
          </div>
        )}
        <div
          key={getKey(current)}
          className={`swipe__card${leaving ? ' is-leaving' : ''}${offset === 0 ? ' is-settled' : ''}`}
          style={{ transform: `translateX(${shift}px) rotate(${shift / 24}deg)` }}
          {...bind}
        >
          {hint && (
            <span className={`swipe__stamp swipe__stamp--${hint}`}>
              {hint === 'like' ? likeLabel : skipLabel}
            </span>
          )}
          {renderCard(current)}
        </div>
      </div>
      <div className="swipe__controls">
        <button
          type="button"
          className="swipe__btn swipe__btn--skip"
          onClick={() => decide('skip')}
        >
          ← {skipLabel}
        </button>
        <span className="swipe__left" aria-live="polite">
          В очереди: {items.length}
        </span>
        <button
          type="button"
          className="swipe__btn swipe__btn--like"
          onClick={() => decide('like')}
        >
          {likeLabel} →
        </button>
      </div>
    </div>
  )
}
