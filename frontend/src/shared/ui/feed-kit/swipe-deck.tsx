import { useEffect, useRef, useState } from 'react'
import type { PointerEvent, ReactNode } from 'react'
import { BurnDissolve } from './burn-dissolve'
import { FilmBurn } from './film-burn'
import heartUrl from './icons/heart.png'
import heartBrokenUrl from './icons/heart-broken.png'
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

const THRESHOLD = 96
const DRAG_START = 6
const TRAVEL_MS = 1080
const DEVELOP_MS = 420
const COOLDOWN_MS = 2000
/**
 * Five frames, each 75% of the gate, so the track is 375% wide.
 * Rest leaves 12.5% of a frame on each side. The spare frame on the left
 * stays in view when the strip rewinds right.
 */
const REST_SHIFT = '-36.6667%'

type Phase = 'idle' | 'develop' | SwipeDecision

/**
 * Flat film gate. Skip carries the strip left and dissolves the card.
 * Like rewinds the strip right under a slow film burn. The arriving text just unblurs.
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
  const [dragging, setDragging] = useState(false)
  const [phase, setPhase] = useState<Phase>('idle')
  const [locked, setLocked] = useState(false)
  const start = useRef<number | null>(null)
  const drag = useRef(0)
  const trackRef = useRef<HTMLDivElement>(null)
  const lockedRef = useRef(false)
  const current = items[0]
  const next = items[1]
  const traveling = phase === 'skip' || phase === 'like'
  const blocked = phase !== 'idle' || locked

  const armCooldown = () => {
    lockedRef.current = true
    setLocked(true)
    window.setTimeout(() => {
      lockedRef.current = false
      setLocked(false)
    }, COOLDOWN_MS)
  }

  const commit = (decision: SwipeDecision) => {
    if (!current || phase !== 'idle' || lockedRef.current) return
    armCooldown()
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (reduce) {
      onDecide(current, decision)
      drag.current = 0
      setOffset(0)
      return
    }
    setPhase(decision)
    window.setTimeout(() => {
      const track = trackRef.current
      if (track) {
        track.style.transition = 'none'
        track.style.transform = `translateX(${REST_SHIFT})`
        void track.offsetWidth
        track.style.transition = ''
      }
      drag.current = 0
      setOffset(0)
      setPhase('develop')
      onDecide(current, decision)
    }, TRAVEL_MS)
    window.setTimeout(() => setPhase('idle'), TRAVEL_MS + DEVELOP_MS)
  }

  const commitRef = useRef(commit)
  const hasItemRef = useRef(false)
  useEffect(() => {
    commitRef.current = commit
    hasItemRef.current = Boolean(current)
  })
  useEffect(() => {
    const onKey = (event: KeyboardEvent) => {
      if (!hasItemRef.current) return
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        document.querySelector('dialog[open]')
      ) {
        return
      }
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
      event.preventDefault()
      commitRef.current(event.key === 'ArrowRight' ? 'like' : 'skip')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [])

  const bind = {
    onPointerDown: (event: PointerEvent<HTMLDivElement>) => {
      if (blocked || (event.target as HTMLElement).closest('.reel__act, button, a, dialog')) return
      start.current = event.clientX
      setDragging(true)
    },
    onPointerMove: (event: PointerEvent<HTMLDivElement>) => {
      if (start.current === null || blocked) return
      const dx = event.clientX - start.current
      if (Math.abs(dx) < DRAG_START) return
      if (!event.currentTarget.hasPointerCapture?.(event.pointerId)) {
        event.currentTarget.setPointerCapture?.(event.pointerId)
      }
      const nextOffset = Math.max(-180, Math.min(120, dx))
      drag.current = nextOffset
      setOffset(nextOffset)
    },
    onPointerUp: () => {
      start.current = null
      setDragging(false)
      if (drag.current >= THRESHOLD) commit('like')
      else if (drag.current <= -THRESHOLD) commit('skip')
      else {
        drag.current = 0
        setOffset(0)
      }
    },
    onPointerCancel: () => {
      start.current = null
      setDragging(false)
      drag.current = 0
      setOffset(0)
    },
  }

  const travel = `translateX(calc(${REST_SHIFT} + ${offset}px))`
  const currentEffect =
    phase === 'skip'
      ? ' is-burn'
      : phase === 'like'
        ? ' is-warm'
        : phase === 'develop'
          ? ' is-develop'
          : ''
  const motionClass = phase === 'skip' ? ' is-advancing' : phase === 'like' ? ' is-rewinding' : ''

  return (
    <div className="reel">
      <div
        className={`reel__gate${current ? '' : ' reel__gate--still'}`}
        {...(current ? bind : {})}
      >
        <div
          ref={trackRef}
          className={`reel__track${dragging ? '' : ' is-settling'}${motionClass}`}
          style={traveling ? undefined : { transform: travel }}
        >
          <div className="reel__cell reel__cell--pad" aria-hidden="true">
            <div className="reel__holes" />
            <div className="reel__window" />
            <div className="reel__holes" />
          </div>
          <div className="reel__cell reel__cell--leader" aria-hidden="true">
            <div className="reel__holes" />
            <div className="reel__window">{next ? renderCard(next) : null}</div>
            <div className="reel__holes" />
          </div>
          <div key={current ? getKey(current) : 'empty'} className={`reel__cell${currentEffect}`}>
            <div className="reel__holes" aria-hidden="true" />
            <div className="reel__window">
              {current ? (
                <>
                  {renderCard(current)}
                  {phase === 'skip' ? <BurnDissolve /> : null}
                  {phase === 'like' ? <FilmBurn /> : null}
                </>
              ) : (
                <div className="reel__placeholder" role="status">
                  {empty}
                </div>
              )}
            </div>
            <div className="reel__holes" aria-hidden="true" />
          </div>
          <div className="reel__cell reel__cell--next" aria-hidden="true">
            <div className="reel__holes" />
            <div className="reel__window">{next ? renderCard(next) : null}</div>
            <div className="reel__holes" />
          </div>
          <div className="reel__cell reel__cell--ahead" aria-hidden="true">
            <div className="reel__holes" />
            <div className="reel__window" />
            <div className="reel__holes" />
          </div>
        </div>

        {current ? (
          <>
            <button
              type="button"
              className="reel__act reel__act--skip"
              onClick={() => commit('skip')}
              disabled={blocked}
            >
              <img src={heartBrokenUrl} alt="" />
              {skipLabel}
            </button>
            <button
              type="button"
              className="reel__act reel__act--like"
              onClick={() => commit('like')}
              disabled={blocked}
            >
              <img src={heartUrl} alt="" />
              {likeLabel}
            </button>
          </>
        ) : null}
      </div>
    </div>
  )
}
