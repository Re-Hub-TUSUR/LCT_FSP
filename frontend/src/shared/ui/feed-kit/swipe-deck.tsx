import { useEffect, useLayoutEffect, useRef, useState } from 'react'
import type { PointerEvent as ReactPointerEvent, ReactNode } from 'react'
import { EditorMark } from './editor-mark'
import heartUrl from './icons/heart.png'
import heartBrokenUrl from './icons/heart-broken.png'
import { ReelEngine } from './reel-engine'
import type { SwipeDecision } from './reel-engine'
import './feed-kit.css'

export type { SwipeDecision }

type Props<T> = {
  items: T[]
  getKey: (item: T) => string
  renderCard: (item: T) => ReactNode
  onDecide: (item: T, decision: SwipeDecision) => void
  likeLabel: string
  skipLabel: string
  empty: ReactNode
}

function Frame({ children }: { children?: ReactNode }) {
  return (
    <div className="reel__cell" aria-hidden="true">
      <div className="reel__holes" />
      <div className="reel__window">
        {children ? <div className="reel__card reel__card--side">{children}</div> : null}
      </div>
      <div className="reel__holes" />
    </div>
  )
}

/**
 * A strip of film in a gate: the current card is the frame in the middle.
 *
 * Skipping burns the frame and runs the strip left; liking gets the frame circled and ticked
 * by the editor's pencil and rewinds the strip right; the next frame then develops. The card
 * follows the pointer, and arrow keys and the two buttons decide as well.
 *
 * Everything that moves is driven by `ReelEngine`, outside React.
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
  const [busy, setBusy] = useState(false)
  const current = items[0]
  const next = items[1]
  const key = current ? getKey(current) : null

  const gate = useRef<HTMLDivElement>(null)
  const track = useRef<HTMLDivElement>(null)
  const frame = useRef<HTMLDivElement>(null)
  const card = useRef<HTMLDivElement>(null)
  const grain = useRef<HTMLDivElement>(null)
  const fx = useRef<HTMLCanvasElement>(null)
  const embers = useRef<HTMLCanvasElement>(null)
  const markSvg = useRef<SVGSVGElement>(null)
  const markCircle = useRef<SVGPathElement>(null)
  const markCheck = useRef<SVGPathElement>(null)
  const markNib = useRef<SVGCircleElement>(null)
  const skipButton = useRef<HTMLButtonElement>(null)
  const skipRing = useRef<HTMLSpanElement>(null)
  const skipIcon = useRef<HTMLImageElement>(null)
  const likeButton = useRef<HTMLButtonElement>(null)
  const likeRing = useRef<HTMLSpanElement>(null)
  const likeIcon = useRef<HTMLImageElement>(null)

  // The decision of the engine goes to whatever card and handler the latest render had.
  const decide = useRef<(decision: SwipeDecision) => void>(() => {})
  useLayoutEffect(() => {
    decide.current = (decision) => {
      if (current) onDecide(current, decision)
    }
  })

  // One engine for the life of the deck; it reads the DOM through the refs on every frame.
  const engine = useRef<ReelEngine | null>(null)
  useLayoutEffect(() => {
    const created = new ReelEngine({
      elements: () => ({
        gate: gate.current,
        track: track.current,
        window: frame.current,
        card: card.current,
        grain: grain.current,
        fx: fx.current,
        embers: embers.current,
        mark:
          markSvg.current && markCircle.current && markCheck.current && markNib.current
            ? {
                svg: markSvg.current,
                circle: markCircle.current,
                check: markCheck.current,
                nib: markNib.current,
              }
            : null,
        skip:
          skipButton.current && skipRing.current && skipIcon.current
            ? { button: skipButton.current, ring: skipRing.current, icon: skipIcon.current }
            : null,
        like:
          likeButton.current && likeRing.current && likeIcon.current
            ? { button: likeButton.current, ring: likeRing.current, icon: likeIcon.current }
            : null,
      }),
      onBusy: (value) => setBusy(value),
      onDecide: (decision) => decide.current(decision),
    })
    engine.current = created
    created.apply()
    return () => {
      created.destroy()
      engine.current = null
    }
  }, [])

  // A new card in the middle: before the browser paints, the strip is back at rest and the
  // frame starts to develop. Otherwise the burnt frame would flash in the centre.
  const shownKey = useRef(key)
  useLayoutEffect(() => {
    if (shownKey.current === key) return
    shownKey.current = key
    engine.current?.afterSwap()
  }, [key])

  useEffect(() => {
    const element = gate.current
    if (!element || typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(() => engine.current?.resized())
    observer.observe(element)
    return () => observer.disconnect()
  }, [])

  const hasCard = Boolean(current)
  useEffect(() => {
    if (!hasCard) return
    const onKey = (event: KeyboardEvent) => {
      if (
        event.target instanceof HTMLInputElement ||
        event.target instanceof HTMLTextAreaElement ||
        // Only a dialog on screen takes the arrows: the header keeps its closed menu in the page.
        document.querySelector(
          'dialog[open], [role="dialog"]:not([aria-hidden="true"]):not([inert])',
        )
      ) {
        return
      }
      if (event.key !== 'ArrowRight' && event.key !== 'ArrowLeft') return
      event.preventDefault()
      engine.current?.commit(event.key === 'ArrowRight' ? 'like' : 'skip')
    }
    window.addEventListener('keydown', onKey)
    return () => window.removeEventListener('keydown', onKey)
  }, [hasCard])

  const pointer = current
    ? {
        onPointerDown: (event: ReactPointerEvent) =>
          engine.current?.onPointerDown(event.nativeEvent),
        onPointerMove: (event: ReactPointerEvent) =>
          engine.current?.onPointerMove(event.nativeEvent),
        onPointerUp: (event: ReactPointerEvent) => engine.current?.onPointerUp(event.nativeEvent),
        onPointerCancel: () => engine.current?.onPointerCancel(),
      }
    : {}

  const hover = (decision: SwipeDecision | null) => (event: ReactPointerEvent) => {
    // Touch has no hover; a finger would leave the ring enlarged.
    if (decision && event.pointerType !== 'mouse') return
    engine.current?.setHover(decision)
  }

  return (
    <div className="reel">
      <div
        ref={gate}
        className={`reel__gate${current ? '' : ' reel__gate--still'}`}
        onDragStart={(event) => event.preventDefault()}
        {...pointer}
      >
        <div ref={track} className="reel__track">
          <Frame />
          <Frame>{next ? renderCard(next) : null}</Frame>
          <div className="reel__cell">
            <div className="reel__holes" aria-hidden="true" />
            <div ref={frame} className="reel__window">
              {current ? (
                <>
                  <div key={key} ref={card} className="reel__card">
                    {renderCard(current)}
                  </div>
                  <div ref={grain} className="reel__grain" aria-hidden="true" />
                  <canvas ref={fx} className="reel__fx" aria-hidden="true" />
                  <EditorMark
                    svgRef={markSvg}
                    circleRef={markCircle}
                    checkRef={markCheck}
                    nibRef={markNib}
                  />
                </>
              ) : (
                <div className="reel__placeholder" role="status">
                  {empty}
                </div>
              )}
            </div>
            <div className="reel__holes" aria-hidden="true" />
          </div>
          <Frame>{next ? renderCard(next) : null}</Frame>
          <Frame />
        </div>
        <canvas ref={embers} className="reel__embers" aria-hidden="true" />
      </div>

      {current ? (
        <div className="reel__acts">
          <button
            ref={skipButton}
            type="button"
            className="reel__act reel__act--skip"
            disabled={busy}
            onClick={() => engine.current?.commit('skip')}
            onPointerEnter={hover('skip')}
            onPointerLeave={hover(null)}
          >
            <span className="reel__disc">
              <span ref={skipRing} className="reel__ring" />
              <img ref={skipIcon} src={heartBrokenUrl} alt="" draggable={false} />
            </span>
            {skipLabel}
          </button>
          <button
            ref={likeButton}
            type="button"
            className="reel__act reel__act--like"
            disabled={busy}
            onClick={() => engine.current?.commit('like')}
            onPointerEnter={hover('like')}
            onPointerLeave={hover(null)}
          >
            <span className="reel__disc">
              <span ref={likeRing} className="reel__ring" />
              <img ref={likeIcon} src={heartUrl} alt="" draggable={false} />
            </span>
            {likeLabel}
          </button>
        </div>
      ) : null}
    </div>
  )
}
