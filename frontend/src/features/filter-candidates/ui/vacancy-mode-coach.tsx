import {
  useEffect,
  useEffectEvent,
  useId,
  useLayoutEffect,
  useRef,
  useState,
  type CSSProperties,
  type RefObject,
} from 'react'
import { createPortal } from 'react-dom'
import { Button } from '@/shared/ui'
import './vacancy-mode-coach.css'

type Side = 'right' | 'below'

type Box = {
  top: number
  left: number
  side: Side
  arrow: number
}

type Hole = {
  top: number
  left: number
  width: number
  height: number
}

type Frame = {
  card: Box
  hole: Hole
}

type Props = {
  anchor: RefObject<HTMLElement | null>
  onLater: () => void
  onNever: () => void
}

type Shade = { key: string; style: CSSProperties }

function shadeBoxes(hole: Hole): Shade[] {
  const width = window.innerWidth
  const height = window.innerHeight
  const right = hole.left + hole.width
  const bottom = hole.top + hole.height
  const boxes: Shade[] = [
    { key: 'top', style: { top: 0, left: 0, width, height: hole.top } },
    { key: 'left', style: { top: hole.top, left: 0, width: hole.left, height: hole.height } },
    {
      key: 'right',
      style: { top: hole.top, left: right, width: width - right, height: hole.height },
    },
    { key: 'bottom', style: { top: bottom, left: 0, width, height: height - bottom } },
  ]
  return boxes.filter((box) => {
    const boxWidth = box.style.width
    const boxHeight = box.style.height
    return (
      typeof boxWidth === 'number' && typeof boxHeight === 'number' && boxWidth > 0 && boxHeight > 0
    )
  })
}

const CARD_WIDTH = 320
const GAP = 18
const MARGIN = 16
// Clear space around the switch so the blur does not eat its border.
const SPOT = 8

/** A one-time note beside the vacancy switch. The page blurs; the switch stays sharp. */
export function VacancyModeCoach({ anchor, onLater, onNever }: Props) {
  const titleId = useId()
  const textId = useId()
  const laterRef = useRef<HTMLButtonElement>(null)
  const neverRef = useRef<HTMLButtonElement>(null)
  const cardRef = useRef<HTMLDivElement>(null)
  const dismiss = useEffectEvent(() => {
    onLater()
  })
  const [frame, setFrame] = useState<Frame | null>(null)

  useLayoutEffect(() => {
    const place = () => {
      const node = anchor.current
      const card = cardRef.current
      if (!node) return
      const rect = node.getBoundingClientRect()
      const width = Math.min(CARD_WIDTH, window.innerWidth - MARGIN * 2)
      const height = card?.offsetHeight ?? 200
      let side: Side = 'right'
      let left = rect.right + GAP
      let top = rect.top + rect.height / 2 - height / 2
      if (left + width > window.innerWidth - MARGIN) {
        side = 'below'
        left = Math.min(Math.max(MARGIN, rect.left), window.innerWidth - width - MARGIN)
        top = rect.bottom + GAP
      }
      top = Math.min(Math.max(MARGIN, top), Math.max(MARGIN, window.innerHeight - height - MARGIN))
      const target =
        side === 'right' ? rect.top + rect.height / 2 - top : rect.left + rect.width / 2 - left
      const arrow = Math.min(Math.max(22, target), (side === 'right' ? height : width) - 22)
      const holeTop = Math.max(0, rect.top - SPOT)
      const holeLeft = Math.max(0, rect.left - SPOT)
      const holeRight = Math.min(window.innerWidth, rect.right + SPOT)
      const holeBottom = Math.min(window.innerHeight, rect.bottom + SPOT)
      setFrame({
        card: { top, left, side, arrow },
        hole: {
          top: holeTop,
          left: holeLeft,
          width: Math.max(0, holeRight - holeLeft),
          height: Math.max(0, holeBottom - holeTop),
        },
      })
    }
    place()
    window.addEventListener('resize', place)
    window.addEventListener('scroll', place, true)
    return () => {
      window.removeEventListener('resize', place)
      window.removeEventListener('scroll', place, true)
    }
  }, [anchor])

  useEffect(() => {
    const previous = document.activeElement
    const overflow = document.body.style.overflow
    document.body.style.overflow = 'hidden'
    laterRef.current?.focus()
    const onKey = (event: KeyboardEvent) => {
      if (event.key === 'Escape') {
        event.preventDefault()
        dismiss()
        return
      }
      if (event.key !== 'Tab') return
      const first = laterRef.current
      const last = neverRef.current
      if (!first || !last) return
      if (event.shiftKey && document.activeElement === first) {
        event.preventDefault()
        last.focus()
      } else if (!event.shiftKey && document.activeElement === last) {
        event.preventDefault()
        first.focus()
      }
    }
    document.addEventListener('keydown', onKey)
    return () => {
      document.body.style.overflow = overflow
      document.removeEventListener('keydown', onKey)
      if (previous instanceof HTMLElement) previous.focus()
    }
  }, [])

  const hole = frame?.hole
  const shades: Shade[] = hole
    ? shadeBoxes(hole)
    : [{ key: 'full', style: { top: 0, left: 0, width: '100%', height: '100%' } }]

  return createPortal(
    <div className="vacancy-coach">
      {shades.map((shade) => (
        <div
          key={shade.key}
          className="vacancy-coach__shade"
          style={shade.style}
          aria-hidden="true"
        />
      ))}
      {hole && (
        <div
          className="vacancy-coach__spot"
          style={{ top: hole.top, left: hole.left, width: hole.width, height: hole.height }}
          aria-hidden="true"
        />
      )}
      <div
        ref={cardRef}
        className="vacancy-coach__card"
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={textId}
        data-side={frame?.card.side ?? 'right'}
        style={
          {
            top: frame?.card.top ?? -9999,
            left: frame?.card.left ?? MARGIN,
            '--arrow': `${frame?.card.arrow ?? 28}px`,
          } as CSSProperties
        }
      >
        <p className="vacancy-coach__kicker">Подсказка</p>
        <h2 id={titleId} className="vacancy-coach__title">
          Выберите вакансию
        </h2>
        <p id={textId} className="vacancy-coach__text">
          Сейчас поиск свободный. Выберите вакансию — покажем кандидатов на эту должность.
        </p>
        <div className="vacancy-coach__actions">
          <Button ref={laterRef} variant="solid" onClick={onLater}>
            Понял
          </Button>
          <Button ref={neverRef} variant="ghost" onClick={onNever}>
            Больше не показывать
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  )
}
