import { useEffect, useRef, useState } from 'react'
import './hacker-text.css'

/** Printable ASCII, the same range the scramble walks: `!` … `~`. */
const ASCII_FIRST = 33
const ASCII_COUNT = 94
const TICK_MS = 40
/** Noise frames every glyph plays before it may become itself. */
const ENCODE_SPINS = 8
/** Extra noise per glyph on a short line, so it still decodes left to right. */
const DECODE_LAG = 3
/** Longest extra wait, in frames, from the first glyph to the last. */
const MAX_DECODE_SPAN = 16

type Props = {
  text: string
  className?: string
  /** Off-screen copy would finish before anyone scrolled to it. */
  whenVisible?: boolean
}

function isGap(char: string): boolean {
  return char.trim() === ''
}

function prefersReducedMotion(): boolean {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false
}

/** A random ASCII glyph, never the real character. */
function noiseGlyph(avoid: string, random: () => number): string {
  const index = Math.floor(random() * ASCII_COUNT)
  const glyph = String.fromCharCode(ASCII_FIRST + index)
  if (glyph !== avoid) return glyph
  return String.fromCharCode(ASCII_FIRST + ((index + 1) % ASCII_COUNT))
}

/**
 * How many noise frames glyph `order` plays (0 = the first real character).
 * Short lines step by `DECODE_LAG`. Long ones squeeze that staircase into
 * `MAX_DECODE_SPAN`, so the tail keeps moving instead of landing in one frame.
 */
function noiseSpins(order: number, glyphCount: number): number {
  if (glyphCount <= 1) return ENCODE_SPINS
  const span = Math.min(DECODE_LAG * (glyphCount - 1), MAX_DECODE_SPAN)
  return ENCODE_SPINS + Math.round((order * span) / (glyphCount - 1))
}

/**
 * Encoder output: each glyph is a queue of noise, then the real character.
 * The further right a glyph sits, the longer its noise, so the decoder settles left to right.
 */
export function encodeQueues(text: string, random: () => number): string[][] {
  let glyphCount = 0
  for (let i = 0; i < text.length; i++) {
    if (!isGap(text.charAt(i))) glyphCount += 1
  }

  const queues: string[][] = []
  let order = 0
  for (let i = 0; i < text.length; i++) {
    const char = text.charAt(i)
    if (isGap(char)) {
      queues.push([char])
      continue
    }
    const spins = noiseSpins(order, glyphCount)
    order += 1
    const queue: string[] = []
    for (let n = 0; n < spins; n++) queue.push(noiseGlyph(char, random))
    queue.push(char)
    queues.push(queue)
  }
  return queues
}

function readQueues(queues: string[][]): string {
  let out = ''
  for (const queue of queues) out += queue[0] ?? ''
  return out
}

/** Drops one noise frame from every glyph that still has some. */
function advance(queues: string[][]): boolean {
  let pending = false
  for (const queue of queues) {
    if (queue.length > 1) {
      queue.shift()
      pending = true
    }
  }
  return pending
}

function HackerRun({ text, className, whenVisible = false }: Props) {
  const nodeRef = useRef<HTMLSpanElement>(null)
  const [queues] = useState<string[][] | null>(() =>
    prefersReducedMotion() || text.length === 0 ? null : encodeQueues(text, Math.random),
  )
  const [shown, setShown] = useState(() => (queues ? readQueues(queues) : text))

  useEffect(() => {
    if (!queues) return

    let interval = 0
    const start = () => {
      const current = queues.map((queue) => queue.slice())
      interval = window.setInterval(() => {
        const pending = advance(current)
        setShown(readQueues(current))
        if (!pending) window.clearInterval(interval)
      }, TICK_MS)
    }

    const node = nodeRef.current
    if (!whenVisible || !node || typeof IntersectionObserver === 'undefined') {
      start()
      return () => window.clearInterval(interval)
    }

    const observer = new IntersectionObserver(
      (entries) => {
        if (!entries.some((entry) => entry.isIntersecting)) return
        observer.disconnect()
        start()
      },
      { threshold: 0.4 },
    )
    observer.observe(node)

    return () => {
      observer.disconnect()
      window.clearInterval(interval)
    }
  }, [queues, whenVisible])

  const classNames = className ? `hacker-text ${className}` : 'hacker-text'

  return (
    <span ref={nodeRef} className={classNames}>
      <span className="visually-hidden">{text}</span>
      <span aria-hidden="true">{shown}</span>
    </span>
  )
}

/**
 * Encodes `text` into ASCII noise, then decodes it left to right.
 * The first frame is already noise, so it starts with the first paint.
 * Colour, size and weight stay whatever the parent already uses.
 */
export function HackerText({ text, className, whenVisible }: Props) {
  return <HackerRun key={text} text={text} className={className} whenVisible={whenVisible} />
}
