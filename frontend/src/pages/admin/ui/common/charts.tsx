import { useId, useState } from 'react'

/*
 * Small SVG charts without a charting library (none is bundled with the app).
 * One series per chart: the title names it, so there is no legend box; the mark color is
 * `--admin-series`, checked for contrast against the page background. Every chart has a
 * hover layer, and the same numbers are always in a table or CSV next to it.
 */

const WIDTH = 640
const HEIGHT = 220
const PAD = { top: 16, right: 16, bottom: 34, left: 44 }
const PLOT_W = WIDTH - PAD.left - PAD.right
const PLOT_H = HEIGHT - PAD.top - PAD.bottom

type Tip = { x: number; y: number; title: string; value: string; hint?: string } | null

function Tooltip({ tip }: { tip: Tip }) {
  if (!tip) return null
  return (
    <div
      className="chart__tip"
      role="status"
      style={{ left: `${(tip.x / WIDTH) * 100}%`, top: `${(tip.y / HEIGHT) * 100}%` }}
    >
      <strong>{tip.title}</strong>
      <span>{tip.value}</span>
      {tip.hint && <span>{tip.hint}</span>}
    </div>
  )
}

function ticks(max: number): number[] {
  const step = max <= 10 ? 2 : max <= 100 ? 25 : Math.ceil(max / 4 / 10) * 10
  const values = []
  for (let value = 0; value <= max + 0.0001; value += step) values.push(value)
  return values
}

/** Labels under a band axis: all of them when they fit, otherwise every n-th. */
function labelEvery(count: number): number {
  return Math.max(1, Math.ceil(count / 8))
}

type LinePoint = { label: string; value: number | null; hint?: string }

type LineProps = {
  title: string
  points: LinePoint[]
  max?: number
  /** A shaded reference zone, e.g. the target solve share. */
  band?: { from: number; to: number; label: string }
  format: (value: number) => string
}

export function LineChart({ title, points, max = 100, band, format }: LineProps) {
  const [tip, setTip] = useState<Tip>(null)
  const titleId = useId()
  const step = points.length > 1 ? PLOT_W / (points.length - 1) : 0
  const x = (index: number) => PAD.left + (points.length > 1 ? index * step : PLOT_W / 2)
  const y = (value: number) => PAD.top + PLOT_H - (Math.min(value, max) / max) * PLOT_H
  const segments: string[] = []
  let current = ''
  points.forEach((point, index) => {
    if (point.value === null) {
      if (current) segments.push(current)
      current = ''
      return
    }
    current += `${current ? 'L' : 'M'}${x(index)},${y(point.value)}`
  })
  if (current) segments.push(current)
  const every = labelEvery(points.length)

  return (
    <figure className="chart">
      <figcaption id={titleId} className="chart__title">
        {title}
      </figcaption>
      <div className="chart__plot" onMouseLeave={() => setTip(null)}>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-labelledby={titleId}>
          {band && (
            <g className="chart__band">
              <rect
                x={PAD.left}
                width={PLOT_W}
                y={y(band.to)}
                height={Math.max(y(band.from) - y(band.to), 0)}
              />
              <text x={PAD.left + PLOT_W - 4} y={y(band.to) + 12} textAnchor="end">
                {band.label}
              </text>
            </g>
          )}
          {ticks(max).map((value) => (
            <g key={value} className="chart__grid">
              <line x1={PAD.left} x2={PAD.left + PLOT_W} y1={y(value)} y2={y(value)} />
              <text x={PAD.left - 8} y={y(value) + 4} textAnchor="end">
                {format(value)}
              </text>
            </g>
          ))}
          {segments.map((path) => (
            <path key={path} className="chart__line" d={path} />
          ))}
          {points.map((point, index) =>
            point.value === null ? null : (
              <circle
                key={point.label}
                className="chart__dot"
                cx={x(index)}
                cy={y(point.value)}
                r={4}
              />
            ),
          )}
          {points.map((point, index) =>
            index % every === 0 || index === points.length - 1 ? (
              <text
                key={`label-${point.label}`}
                className="chart__axis"
                x={x(index)}
                y={HEIGHT - 12}
                textAnchor="middle"
              >
                {point.label}
              </text>
            ) : null,
          )}
          {tip && (
            <line
              className="chart__crosshair"
              x1={tip.x}
              x2={tip.x}
              y1={PAD.top}
              y2={PAD.top + PLOT_H}
            />
          )}
          {points.map((point, index) => (
            <rect
              key={`hit-${point.label}`}
              className="chart__hit"
              x={x(index) - Math.max(step, 24) / 2}
              y={PAD.top}
              width={Math.max(step, 24)}
              height={PLOT_H}
              onMouseEnter={() =>
                setTip({
                  x: x(index),
                  y: point.value === null ? PAD.top + PLOT_H / 2 : y(point.value),
                  title: point.label,
                  value: point.value === null ? 'нет попыток' : format(point.value),
                  hint: point.hint,
                })
              }
            />
          ))}
        </svg>
        <Tooltip tip={tip} />
      </div>
    </figure>
  )
}

type Bar = { label: string; value: number; hint?: string }

type BarProps = {
  title: string
  bars: Bar[]
  max?: number
  format: (value: number) => string
  /** Value labels above the bars: only when there are few of them. */
  labelled?: boolean
}

export function BarChart({ title, bars, max, format, labelled = bars.length <= 8 }: BarProps) {
  const [tip, setTip] = useState<Tip>(null)
  const titleId = useId()
  const top = max ?? Math.max(1, ...bars.map((bar) => bar.value))
  const slot = bars.length ? PLOT_W / bars.length : PLOT_W
  // Thin marks with a 2px gap between neighbours.
  const width = Math.max(Math.min(slot - 2, 48), 2)
  const y = (value: number) => PAD.top + PLOT_H - (value / top) * PLOT_H
  const every = labelEvery(bars.length)

  return (
    <figure className="chart">
      <figcaption id={titleId} className="chart__title">
        {title}
      </figcaption>
      <div className="chart__plot" onMouseLeave={() => setTip(null)}>
        <svg viewBox={`0 0 ${WIDTH} ${HEIGHT}`} role="img" aria-labelledby={titleId}>
          {ticks(top).map((value) => (
            <g key={value} className="chart__grid">
              <line x1={PAD.left} x2={PAD.left + PLOT_W} y1={y(value)} y2={y(value)} />
              <text x={PAD.left - 8} y={y(value) + 4} textAnchor="end">
                {format(value)}
              </text>
            </g>
          ))}
          {bars.map((bar, index) => {
            const left = PAD.left + index * slot + (slot - width) / 2
            const height = Math.max(PAD.top + PLOT_H - y(bar.value), bar.value > 0 ? 2 : 0)
            const radius = Math.min(4, width / 2, height)
            // Rounded data end, square at the baseline.
            const path = `M${left},${PAD.top + PLOT_H}
              V${PAD.top + PLOT_H - height + radius}
              Q${left},${PAD.top + PLOT_H - height} ${left + radius},${PAD.top + PLOT_H - height}
              H${left + width - radius}
              Q${left + width},${PAD.top + PLOT_H - height} ${left + width},${PAD.top + PLOT_H - height + radius}
              V${PAD.top + PLOT_H}Z`
            return (
              <g key={bar.label}>
                <path className="chart__bar" d={path} />
                {labelled && bar.value > 0 && (
                  <text
                    className="chart__value"
                    x={left + width / 2}
                    y={PAD.top + PLOT_H - height - 6}
                    textAnchor="middle"
                  >
                    {format(bar.value)}
                  </text>
                )}
                {(index % every === 0 || index === bars.length - 1) && (
                  <text
                    className="chart__axis"
                    x={left + width / 2}
                    y={HEIGHT - 12}
                    textAnchor="middle"
                  >
                    {bar.label}
                  </text>
                )}
                <rect
                  className="chart__hit"
                  x={PAD.left + index * slot}
                  y={PAD.top}
                  width={slot}
                  height={PLOT_H}
                  onMouseEnter={() =>
                    setTip({
                      x: left + width / 2,
                      y: PAD.top + PLOT_H - height,
                      title: bar.label,
                      value: format(bar.value),
                      hint: bar.hint,
                    })
                  }
                />
              </g>
            )
          })}
        </svg>
        <Tooltip tip={tip} />
      </div>
    </figure>
  )
}

type FunnelStep = { label: string; count: number | null; share: number | null }

/** Horizontal bars: each step against the first one. */
export function Funnel({ title, steps }: { title: string; steps: FunnelStep[] }) {
  const first = steps[0]?.count || 0
  return (
    <figure className="funnel">
      <figcaption className="chart__title">{title}</figcaption>
      <ol className="funnel__steps">
        {steps.map((step) => {
          const width = step.count !== null && first ? (step.count / first) * 100 : 0
          return (
            <li key={step.label} className="funnel__step">
              <span className="funnel__label">{step.label}</span>
              <span className="funnel__track" aria-hidden="true">
                <span className="funnel__fill" style={{ width: `${width}%` }} />
              </span>
              <span className="funnel__value">
                {step.count === null ? 'нет данных' : step.count.toLocaleString('ru-RU')}
                {step.share !== null && step.count !== null && (
                  <span className="funnel__share"> · {step.share.toLocaleString('ru-RU')}%</span>
                )}
              </span>
            </li>
          )
        })}
      </ol>
    </figure>
  )
}
