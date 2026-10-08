import type { ReactNode } from 'react'
import './ornament.css'

type Tone = 'b' | 'w' | 'r'

/**
 * Shapes of the ФСП «hybrid patterns» that no typeface has: the meander, the wave, the zigzag,
 * the triangle over a triangle, three dots, the arrow and the node on a wire.
 * Each is drawn on a 20-unit-high box and takes the colour of its tone.
 */
const SHAPES = {
  meander: {
    width: 24,
    draw: (
      <path
        d="M0 2h24v4H0zM0 8h5v4H0zM13 6h5v9h-5zM5 15h19v4H5z"
        fill="currentColor"
        stroke="none"
      />
    ),
  },
  wave: {
    width: 36,
    draw: <path d="M1 7q4.25 9 8.5 0q4.25 9 8.5 0q4.25 9 8.5 0q4.25 9 8.5 0" strokeWidth="4" />,
  },
  zigzag: {
    width: 24,
    draw: <path d="M1 14l5.5-7 5.5 7 5.5-7 5.5 7" strokeWidth="3.6" />,
  },
  peak: {
    width: 20,
    draw: (
      <>
        <path d="M10 1l9 12H1z" fill="currentColor" stroke="none" />
        <path d="M10 14l4.5 5.5h-9z" fill="var(--red)" stroke="none" />
      </>
    ),
  },
  triad: {
    width: 18,
    draw: (
      <g fill="currentColor" stroke="none">
        <circle cx="9" cy="5" r="3.2" />
        <circle cx="4" cy="15" r="3.2" />
        <circle cx="14" cy="15" r="3.2" />
      </g>
    ),
  },
  arrow: {
    width: 24,
    draw: <path d="M23 10H3M10 3l-7 7 7 7" strokeWidth="3.4" />,
  },
  node: {
    width: 24,
    draw: (
      <>
        <circle cx="8" cy="10" r="7" fill="currentColor" stroke="none" />
        <path d="M14 10h10" strokeWidth="3.4" />
      </>
    ),
  },
  bar: {
    width: 22,
    draw: <path d="M0 8h22v5H0z" fill="currentColor" stroke="none" />,
  },
  dot: {
    width: 16,
    draw: <circle cx="8" cy="10" r="7" fill="currentColor" stroke="none" />,
  },
} as const satisfies Record<string, { width: number; draw: ReactNode }>

type Shape = keyof typeof SHAPES

/** One piece of a sign: a glyph of the typeface or a drawn shape, in its tone. */
type Part = { glyph: string; tone: Tone } | { shape: Shape; tone: Tone }

/** A sign of the ornament: parts set tight, as one unit of the rhythm. */
type Sign = readonly Part[]

const g = (glyph: string, tone: Tone): Part => ({ glyph, tone })
const s = (shape: Shape, tone: Tone): Part => ({ shape, tone })

/** The alphabet of the brandbook's hybrid patterns, in the order of its sample friezes. */
const ALPHABET: readonly Sign[] = [
  [s('dot', 'r')],
  [s('meander', 'b')],
  [g('{', 'w'), g('•', 'r'), g('}', 'w')],
  [s('peak', 'b')],
  [s('meander', 'b')],
  [g('{', 'r'), g('//', 'w'), g('}', 'r')],
  [s('dot', 'r')],
  [g('<', 'b'), g('/', 'r'), g('>', 'b')],
  [g('(', 'b'), g(')', 'b')],
  [g('>', 'b'), g('|', 'w'), g('<', 'b')],
  [s('bar', 'b')],
  [s('peak', 'w')],
  [s('wave', 'b')],
  [g(':', 'w'), g(')', 'b')],
  [g('//', 'r')],
  [s('zigzag', 'r')],
  [s('triad', 'w')],
  [s('arrow', 'b')],
  [g('[', 'b'), g('•', 'w'), g('/', 'r'), g(']', 'b')],
  [s('node', 'w')],
  [g('{', 'b'), g('}', 'b')],
  [g('•', 'w')],
  [g('|', 'r')],
  [g('>', 'b')],
  [g('•', 'w')],
  [g('|', 'b')],
  [g('<', 'b'), g('/', 'r'), g('>', 'b')],
  [g('<', 'b'), g('//', 'r'), g('>', 'b')],
]

function PartView({ part }: { part: Part }) {
  if ('glyph' in part) {
    return <span className={`ornament__g ornament__g--${part.tone}`}>{part.glyph}</span>
  }
  const shape = SHAPES[part.shape]
  return (
    <svg
      className={`ornament__shape ornament__g--${part.tone}`}
      viewBox={`0 0 ${shape.width} 20`}
      style={{ aspectRatio: `${shape.width} / 20` }}
      fill="none"
      stroke="currentColor"
    >
      {shape.draw}
    </svg>
  )
}

function SignView({ sign, flip = false }: { sign: Sign; flip?: boolean }) {
  return (
    <span className={flip ? 'ornament__sign ornament__sign--flip' : 'ornament__sign'}>
      {sign.map((part, index) => (
        // Parts of a sign are a fixed list: position is their identity.
        <PartView key={`part-${index}`} part={part} />
      ))}
    </span>
  )
}

type Props = {
  /**
   * `run` repeats the alphabet; `mirror` is a frieze that reads the same from both ends.
   * Both are longer than any container and are clipped by it, so they span its full width.
   */
  variant?: 'run' | 'mirror'
  /** Signs in a `run` strip, or in one half of a `mirror` frieze. */
  length?: number
  className?: string
}

/** Decorative frieze of the ФСП signs. Clipped by its container, never read aloud. */
export function Ornament({ variant = 'run', length, className }: Props) {
  const count = length ?? (variant === 'mirror' ? 36 : 48)
  const signs = Array.from({ length: count }, (_, index) => ALPHABET[index % ALPHABET.length]!)

  return (
    <div
      className={['ornament', `ornament--${variant}`, className].filter(Boolean).join(' ')}
      aria-hidden="true"
    >
      {variant === 'mirror' ? (
        <>
          {/* The left half is the right one seen in a mirror: every sign is flipped. */}
          <span className="ornament__half ornament__half--left">
            {signs.map((sign, index) => (
              <SignView key={`left-${index}`} sign={sign} flip />
            ))}
          </span>
          <span className="ornament__g ornament__g--w ornament__axis">•</span>
          <span className="ornament__half">
            {signs.map((sign, index) => (
              <SignView key={`right-${index}`} sign={sign} />
            ))}
          </span>
        </>
      ) : (
        signs.map((sign, index) => <SignView key={`sign-${index}`} sign={sign} />)
      )}
    </div>
  )
}
