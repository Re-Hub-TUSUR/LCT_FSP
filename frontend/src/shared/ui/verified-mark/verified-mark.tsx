import { useId, useState } from 'react'
import './verified-mark.css'

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
      <circle cx="8" cy="8" r="8" />
      <path d="M4.6 8.3 7 10.6l4.4-4.9" />
    </svg>
  )
}

/** Check mark next to a company name, like a verified account in Telegram. */
export function VerifiedMark({ text = DEFAULT_TEXT, interactive = true }: Props) {
  const id = useId()
  const [open, setOpen] = useState(false)

  if (!interactive) {
    return (
      <span className="verified-mark verified-mark--static">
        <Check />
        <span className="verified-mark__tip" aria-hidden="true">
          {text}
        </span>
        <span className="visually-hidden">{text}</span>
      </span>
    )
  }

  return (
    <span
      className="verified-mark"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      <button
        type="button"
        className="verified-mark__button"
        aria-label="IT-аккредитация"
        aria-describedby={id}
        onFocus={() => setOpen(true)}
        onBlur={() => setOpen(false)}
        onClick={(event) => {
          // A tap shows the hint; the card around must not react to it.
          event.stopPropagation()
          setOpen(true)
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
      <span id={id} role="tooltip" className="verified-mark__tip" data-open={open || undefined}>
        {text}
      </span>
    </span>
  )
}
