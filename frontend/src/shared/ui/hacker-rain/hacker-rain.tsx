import { useEffect, useRef, useState, type CSSProperties } from 'react'
import './hacker-rain.css'

/** Printable ASCII, the same range `HackerText` scrambles: `!` … `~`. */
const ASCII_FIRST = 33
const ASCII_COUNT = 94
/**
 * `HackerText` steps every 40ms. The rain walks the same noise, stretched so each
 * glyph is readable instead of flickering past.
 */
const TICK_MS = 90
/** Noise frames in one scramble, the same run `HackerText` gives a glyph before it may settle. */
const SCRAMBLE_SPINS = 8
/** Quiet frames after a scramble: about 1.1–2.2s of a still glyph. */
const HOLD_MIN = 8
const HOLD_SPAN = 8

const DEFAULT_COUNT = 200

/** The three tones of the brandbook, the same ones the ornament paints. */
const TONES = ['ink', 'blue', 'red'] as const
type Tone = (typeof TONES)[number]

type Drop = {
  id: number
  glyph: string
  tone: Tone
  left: number
  duration: number
  delay: number
  size: number
  opacity: number
  drift: number
}

type Props = {
  /** How many single glyphs share the field. They are staggered, so only some are visible at once. */
  count?: number
  className?: string
}

function prefersReducedMotion(): boolean {
  return window.matchMedia?.('(prefers-reduced-motion: reduce)')?.matches ?? false
}

function glyph(random: () => number): string {
  return String.fromCharCode(ASCII_FIRST + Math.floor(random() * ASCII_COUNT))
}

function toneOf(random: () => number): Tone {
  return TONES[Math.floor(random() * TONES.length)] ?? 'ink'
}

/**
 * Ink stays a whisper. Blue and red need a little more opacity or the hue
 * disappears into the ground, and they still sit well under the interface.
 */
function peakOpacity(tone: Tone, random: () => number): number {
  if (tone === 'ink') return 0.06 + random() * 0.07
  return 0.27 + random() * 0.1
}

/** A random ASCII glyph, never the one on screen. Same step `HackerText` uses. */
function noiseGlyph(avoid: string, random: () => number): string {
  const index = Math.floor(random() * ASCII_COUNT)
  const next = String.fromCharCode(ASCII_FIRST + index)
  if (next !== avoid) return next
  return String.fromCharCode(ASCII_FIRST + ((index + 1) % ASCII_COUNT))
}

type Cell = {
  glyph: string
  /** Noise frames still to play. Zero means the glyph is holding. */
  spins: number
  /** Quiet frames left before the next scramble. */
  hold: number
}

function holdFrames(random: () => number): number {
  return HOLD_MIN + Math.floor(random() * HOLD_SPAN)
}

/** One tick of a drop: either it rests, or it walks one HackerText noise frame. */
function stepCell(cell: Cell, random: () => number): Cell {
  if (cell.hold > 0) return { ...cell, hold: cell.hold - 1 }
  const next = noiseGlyph(cell.glyph, random)
  if (cell.spins > 1) return { glyph: next, spins: cell.spins - 1, hold: 0 }
  return { glyph: next, spins: 0, hold: holdFrames(random) }
}

/** Spread drops across the width so they do not stack into a column. */
function place(count: number, random: () => number): number[] {
  const lefts: number[] = []
  const gap = Math.min(8, 70 / count)
  let guard = 0
  while (lefts.length < count && guard < count * 40) {
    guard += 1
    const left = 3 + random() * 94
    if (lefts.every((other) => Math.abs(other - left) > gap)) lefts.push(left)
  }
  while (lefts.length < count) lefts.push(3 + random() * 94)
  return lefts
}

function makeCells(drops: Drop[], random: () => number): Cell[] {
  return drops.map((drop) => {
    const spins = random() < 0.5 ? 1 + Math.floor(random() * SCRAMBLE_SPINS) : 0
    return {
      glyph: drop.glyph,
      spins,
      hold: spins === 0 ? holdFrames(random) : 0,
    }
  })
}

function makeDrops(count: number, random: () => number): Drop[] {
  return place(count, random).map((left, id) => {
    const duration = 16 + random() * 18
    const tone = toneOf(random)
    return {
      id,
      glyph: glyph(random),
      tone,
      left,
      duration,
      delay: -random() * duration,
      size: 11 + Math.floor(random() * 3),
      opacity: peakOpacity(tone, random),
      drift: (random() - 0.5) * 14,
    }
  })
}

function Rain({ count, className }: { count: number; className?: string }) {
  const [drops] = useState(() => makeDrops(count, Math.random))
  const [cells, setCells] = useState(() => makeCells(drops, Math.random))
  const cellsRef = useRef(cells)
  const classNames = className ? `hacker-rain ${className}` : 'hacker-rain'

  useEffect(() => {
    const id = window.setInterval(() => {
      const current = cellsRef.current
      const next = current.map((cell) => stepCell(cell, Math.random))
      cellsRef.current = next
      if (next.some((cell, index) => cell.glyph !== current[index]?.glyph)) setCells(next)
    }, TICK_MS)
    return () => window.clearInterval(id)
  }, [])

  return (
    <div className={classNames} aria-hidden="true">
      {drops.map((drop, index) => (
        <span
          key={drop.id}
          className={`hacker-rain__drop hacker-rain__drop--${drop.tone}`}
          style={
            {
              '--x': `${drop.left}%`,
              '--dur': `${drop.duration}s`,
              '--delay': `${drop.delay}s`,
              '--size': `${drop.size}px`,
              '--a': drop.opacity,
              '--drift': `${drop.drift}px`,
            } as CSSProperties
          }
        >
          {cells[index]?.glyph}
        </span>
      ))}
    </div>
  )
}

/**
 * A sparse field of single ASCII glyphs drifting from the bottom edge upward.
 * Each glyph is one character. It rests, then walks the same ASCII noise
 * `HackerText` uses, slowly enough to read each frame.
 *
 * The field is fixed to the viewport, so glyphs start at the bottom edge
 * and cross the whole page. An isolated ancestor keeps them behind that
 * page's content and above the ground.
 */
export function HackerRain({ count = DEFAULT_COUNT, className }: Props) {
  const [reduced] = useState(prefersReducedMotion)
  if (reduced || count < 1) return null
  return <Rain count={count} className={className} />
}
