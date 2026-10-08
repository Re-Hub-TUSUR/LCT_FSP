import { useId } from 'react'
import type { Ref } from 'react'

const clamp = (value: number, min: number, max: number) => Math.min(max, Math.max(min, value))
/** One decimal is plenty for a path coordinate. */
const n = (value: number) => value.toFixed(1)

export type MarkParts = {
  svg: SVGSVGElement
  circle: SVGPathElement
  check: SVGPathElement
  nib: SVGCircleElement
}

/** Path lengths of a laid-out mark, for drawing it stroke by stroke. */
export type MarkGeometry = { circleLength: number; checkLength: number }

type Props = {
  svgRef: Ref<SVGSVGElement>
  circleRef: Ref<SVGPathElement>
  checkRef: Ref<SVGPathElement>
  nibRef: Ref<SVGCircleElement>
}

/**
 * The film editor's mark on a frame that is liked: a wax pencil circles the frame with an
 * uneven oval and ticks it. The paths are laid out and drawn by `layoutMark` / `paintMark`.
 */
export function EditorMark({ svgRef, circleRef, checkRef, nibRef }: Props) {
  // `useId` may contain characters that do not survive inside `url(#…)`.
  const wax = `wax-${useId().replace(/[^a-zA-Z0-9_-]/g, '')}`
  return (
    <svg ref={svgRef} className="reel__mark" aria-hidden="true">
      <defs>
        {/* The grain of a wax pencil on film. */}
        <filter id={wax} x="-5%" y="-5%" width="110%" height="110%">
          <feTurbulence
            type="fractalNoise"
            baseFrequency="0.85"
            numOctaves="2"
            seed="7"
            result="grain"
          />
          <feDisplacementMap
            in="SourceGraphic"
            in2="grain"
            scale="2.4"
            xChannelSelector="R"
            yChannelSelector="G"
          />
        </filter>
      </defs>
      <g
        filter={`url(#${wax})`}
        fill="none"
        stroke="#7d72ff"
        strokeLinecap="round"
        strokeLinejoin="round"
      >
        <path ref={circleRef} d="M0 0" />
        <path ref={checkRef} d="M0 0" />
      </g>
      <circle ref={nibRef} className="reel__nib" cx="0" cy="0" r="3" />
    </svg>
  )
}

/**
 * Lays the mark out for a frame of the given size. The oval overlaps itself and wobbles
 * differently every time, like a hand would draw it. Null where SVG geometry is not
 * available (jsdom) or the frame has no size yet.
 */
export function layoutMark(
  { svg, circle, check, nib }: MarkParts,
  width: number,
  height: number,
): MarkGeometry | null {
  if (!width || !height || typeof circle.getTotalLength !== 'function') return null
  svg.setAttribute('viewBox', `0 0 ${width} ${height}`)

  const random = Math.random
  const cx = width * (0.5 + (random() - 0.5) * 0.02)
  const cy = height * (0.48 + (random() - 0.5) * 0.02)
  const rx = width * 0.445
  const ry = height * 0.43
  const start = -Math.PI * (0.62 + random() * 0.08)
  const turn = Math.PI * 2 * (1.1 + random() * 0.05)
  const phase1 = random() * 6.28
  const phase2 = random() * 6.28
  const points: string[] = []
  const steps = 96
  for (let i = 0; i <= steps; i += 1) {
    const u = i / steps
    const angle = start + turn * u
    const wobble =
      1 + 0.035 * Math.sin(3 * angle + phase1) + 0.018 * Math.sin(5 * angle + phase2) + 0.045 * u
    points.push(
      `${(cx + Math.cos(angle) * rx * wobble).toFixed(1)} ${(cy + Math.sin(angle) * ry * wobble).toFixed(1)}`,
    )
  }
  circle.setAttribute('d', `M${points.join(' L')}`)

  // The tick: two curves through A → B → C in the top right corner.
  const size = Math.min(width, height) * 0.17
  const kx = width * 0.83
  const ky = height * 0.17
  const a = [kx - size * 0.5, ky + size * 0.02] as const
  const b = [kx - size * 0.12, ky + size * 0.42] as const
  const c = [kx + size * 0.62, ky - size * 0.5] as const
  const bend = [(b[0] + c[0]) / 2 - size * 0.06, (b[1] + c[1]) / 2 + size * 0.02] as const
  check.setAttribute(
    'd',
    `M${n(a[0])} ${n(a[1])} Q${n(a[0] + size * 0.12)} ${n(b[1] - size * 0.12)} ${n(b[0])} ${n(b[1])} ` +
      `Q${n(bend[0])} ${n(bend[1])} ${n(c[0])} ${n(c[1])}`,
  )

  const stroke = clamp(Math.min(width, height) * 0.016, 3.5, 7)
  circle.setAttribute('stroke-width', stroke.toFixed(2))
  check.setAttribute('stroke-width', (stroke * 1.15).toFixed(2))
  nib.setAttribute('r', (stroke * 0.6).toFixed(2))
  return { circleLength: circle.getTotalLength(), checkLength: check.getTotalLength() }
}

/** Shows the first `progress` (0..1) of a path, as if it were being drawn. */
function drawStroke(path: SVGPathElement, length: number, progress: number) {
  path.style.opacity = progress > 0 ? '0.94' : '0'
  path.style.strokeDasharray = `${length} ${length}`
  path.style.strokeDashoffset = String(length * (1 - progress))
}

/** Draws the first `mark` (0..1) of the oval and `tick` (0..1) of the tick; 0 hides them. */
export function paintMark(
  { circle, check, nib }: MarkParts,
  geometry: MarkGeometry | null,
  mark: number,
  tick: number,
) {
  if (!geometry || (!mark && !tick)) {
    circle.style.opacity = '0'
    check.style.opacity = '0'
    nib.style.opacity = '0'
    return
  }
  drawStroke(circle, geometry.circleLength, mark)
  drawStroke(check, geometry.checkLength, tick)

  // The pencil tip rides the end of the stroke while it is being drawn.
  let tip: DOMPoint | null = null
  if (tick > 0 && tick < 1) tip = check.getPointAtLength(geometry.checkLength * tick)
  else if (mark > 0 && mark < 1) tip = circle.getPointAtLength(geometry.circleLength * mark)
  if (tip) {
    nib.setAttribute('cx', tip.x.toFixed(1))
    nib.setAttribute('cy', tip.y.toFixed(1))
    nib.style.opacity = '1'
  } else {
    nib.style.opacity = '0'
  }
}
