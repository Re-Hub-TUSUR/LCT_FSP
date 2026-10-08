import './ornament.css'

type Tone = 'b' | 'w' | 'r'
type Glyph = readonly [string, Tone]

/** The ФСП ornament: brackets, dots and slashes in blue, light and red. */
const RUN: readonly Glyph[] = [
  ['{', 'b'],
  ['•', 'w'],
  ['}', 'b'],
  ['|', 'r'],
  ['>', 'b'],
  ['•', 'w'],
  ['|', 'b'],
  ['<', 'b'],
  ['/', 'r'],
  ['>', 'b'],
  ['▲', 'w'],
  ['[', 'b'],
  ['•', 'w'],
  [']', 'b'],
  ['//', 'r'],
  ['●', 'r'],
  ['—', 'b'],
]

const HALF: readonly Glyph[] = [
  ['●', 'r'],
  ['—', 'b'],
  ['>', 'b'],
  ['|', 'w'],
  ['<', 'b'],
  ['/', 'r'],
  ['>', 'b'],
  ['▲', 'w'],
  ['{', 'b'],
  ['•', 'r'],
  ['}', 'b'],
  ['|', 'r'],
  ['[', 'b'],
  ['•', 'w'],
  [']', 'b'],
  ['//', 'r'],
]

const MIRROR: Record<string, string> = {
  '{': '}',
  '}': '{',
  '[': ']',
  ']': '[',
  '<': '>',
  '>': '<',
  '/': '\\',
  '//': '\\\\',
}

/** One half, a dot, and the same half reflected: the strip reads the same from both ends. */
const SYMMETRIC: readonly Glyph[] = [
  ...HALF,
  ['•', 'w'],
  ...HALF.reduceRight<Glyph[]>(
    (mirrored, [glyph, tone]) => [...mirrored, [MIRROR[glyph] ?? glyph, tone]],
    [],
  ),
]

type Props = {
  /** `run` repeats the sequence to fill the line, `mirror` is one symmetric strip. */
  variant?: 'run' | 'mirror'
  /** Glyphs in a `run` strip. */
  length?: number
  className?: string
}

/** Decorative strip of glyphs. Clipped by its container, never read aloud. */
export function Ornament({ variant = 'run', length = 40, className }: Props) {
  const glyphs =
    variant === 'mirror'
      ? SYMMETRIC
      : Array.from({ length }, (_, index) => RUN[index % RUN.length]!)

  return (
    <div className={className ? `ornament ${className}` : 'ornament'} aria-hidden="true">
      {glyphs.map(([glyph, tone], index) => (
        // The strip is static: position is the identity of a glyph.
        <span key={`${index}-${glyph}`} className={`ornament__g ornament__g--${tone}`}>
          {glyph}
        </span>
      ))}
    </div>
  )
}
