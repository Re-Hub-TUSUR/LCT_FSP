import { useId, useRef, useState } from 'react'
import './verified-mark.css'

const EDGE = 8

/** The box the hint must fit in: the nearest ancestor that clips (a side sheet), or the window. */
function clipBox(from: HTMLElement): { left: number; right: number } {
  let left = 0
  let right = window.innerWidth
  for (let node = from.parentElement; node; node = node.parentElement) {
    if (getComputedStyle(node).overflowX !== 'visible') {
      const box = node.getBoundingClientRect()
      left = Math.max(left, box.left)
      right = Math.min(right, box.right)
      break
    }
  }
  return { left, right }
}

/** Centred under the mark, then moved sideways just enough to stay whole. */
function fitTip(tip: HTMLElement | null) {
  if (!tip) return
  tip.style.setProperty('--tip-shift', '0px')
  const box = tip.getBoundingClientRect()
  const bounds = clipBox(tip)
  let shift = 0
  if (box.left < bounds.left + EDGE) shift = bounds.left + EDGE - box.left
  else if (box.right > bounds.right - EDGE) shift = bounds.right - EDGE - box.right
  tip.style.setProperty('--tip-shift', `${Math.round(shift)}px`)
}

const DEFAULT_TEXT = 'Компания подтвердила IT-аккредитацию Минцифры'

type Props = {
  text?: string
  /**
   * False inside another control (a card that is a button): the mark is then a picture with
   * the text for screen readers, and the hint shows on hover only.
   */
  interactive?: boolean
}

function Check() {
  return (
    <svg className="verified-mark__icon" viewBox="0 0 16 16" aria-hidden="true" focusable="false">
      <rect width="16" height="16" />
      <path d="M4.6 8.3 7 10.6l4.4-4.9" />
    </svg>
  )
}

/** Check mark next to a company name: a blue square with a tick, as in the ФСП style. */
export function VerifiedMark({ text = DEFAULT_TEXT, interactive = true }: Props) {
  const id = useId()
  const [open, setOpen] = useState(false)
  const tip = useRef<HTMLSpanElement>(null)
  const show = () => {
    fitTip(tip.current)
    setOpen(true)
  }

  if (!interactive) {
    return (
      <span
        className="verified-mark verified-mark--static"
        onMouseEnter={() => fitTip(tip.current)}
      >
        <Check />
        <span ref={tip} className="verified-mark__tip" aria-hidden="true">
          {text}
        </span>
        <span className="visually-hidden">{text}</span>
      </span>
    )
  }

  return (
    <span className="verified-mark" onMouseEnter={show} onMouseLeave={() => setOpen(false)}>
      <button
        type="button"
        className="verified-mark__button"
        aria-label="IT-аккредитация"
        aria-describedby={id}
        onFocus={show}
        onBlur={() => setOpen(false)}
        onClick={(event) => {
          // A tap shows the hint; the card around must not react to it.
          event.stopPropagation()
          show()
        }}
        onKeyDown={(event) => {
          if (event.key === 'Escape' && open) {
            event.stopPropagation()
            setOpen(false)
          }
        }}
      >
        <Check />
      </button>
      <span
        ref={tip}
        id={id}
        role="tooltip"
        className="verified-mark__tip"
        data-open={open || undefined}
      >
        {text}
      </span>
    </span>
  )
}
