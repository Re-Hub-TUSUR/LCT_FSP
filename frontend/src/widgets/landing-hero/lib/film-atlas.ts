import { INK, SCRIPTS, type FilmScript, type InkKind } from '../config/film-scripts'

// 135 film proportions: 8 perforations per frame, 36x24 image on a 35mm strip, 38mm pitch
const CELL_W = 608
const CELL_H = 560
const COLS = 4
const ROWS = 4
const MARGIN = Math.round(CELL_H * 0.157)
const HOLE_W = Math.round(CELL_W * 0.052)
const HOLE_H = Math.round(CELL_H * 0.08)
const SLOT = CELL_W / 8
const IMG_X = Math.round(CELL_W / 38)

export const FRAME_PITCH = CELL_W / CELL_H
export const ATLAS_FONTS = ['400 14px "IBM Plex Mono"', '500 13px "IBM Plex Mono"'] as const

/** 4x4 atlas of film frames: base, code still, edge markings, perforations cut to alpha 0. */
export function paintAtlas() {
  const canvas = document.createElement('canvas')
  canvas.width = CELL_W * COLS
  canvas.height = CELL_H * ROWS
  const ctx = canvas.getContext('2d')
  if (!ctx) return null
  const rnd = rng(7)
  SCRIPTS.slice(0, COLS * ROWS).forEach((script, index) => {
    ctx.save()
    ctx.translate((index % COLS) * CELL_W, Math.floor(index / COLS) * CELL_H)
    paintCell(ctx, script, index, rnd)
    ctx.restore()
  })
  paintWear(ctx, canvas.width, canvas.height, rnd)
  return canvas
}

function rng(seed: number) {
  return () => {
    seed |= 0
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}

function paintCell(
  ctx: CanvasRenderingContext2D,
  script: FilmScript,
  index: number,
  rnd: () => number,
) {
  const W = CELL_W
  const H = CELL_H
  ctx.fillStyle = '#14171f'
  ctx.fillRect(0, 0, W, H)
  const base = ctx.createLinearGradient(0, 0, 0, H)
  base.addColorStop(0, 'rgba(255,255,255,0.03)')
  base.addColorStop(0.5, 'rgba(0,0,0,0)')
  base.addColorStop(1, 'rgba(255,255,255,0.02)')
  ctx.fillStyle = base
  ctx.fillRect(0, 0, W, H)

  const iw = W - IMG_X * 2
  const ih = H - MARGIN * 2
  ctx.save()
  roundRect(ctx, IMG_X, MARGIN, iw, ih, 9)
  ctx.clip()
  const lift = 0.85 + rnd() * 0.3
  ctx.fillStyle = '#0a0d15'
  ctx.fillRect(IMG_X, MARGIN, iw, ih)
  const vignette = ctx.createRadialGradient(W / 2, H / 2, ih * 0.1, W / 2, H / 2, iw * 0.62)
  vignette.addColorStop(0, `rgba(40,48,72,${0.22 * lift})`)
  vignette.addColorStop(1, 'rgba(0,0,0,0.35)')
  ctx.fillStyle = vignette
  ctx.fillRect(IMG_X, MARGIN, iw, ih)
  paintCode(ctx, script, IMG_X, MARGIN, iw, ih)
  ctx.restore()
  ctx.strokeStyle = 'rgba(0,0,0,0.55)'
  ctx.lineWidth = 2
  roundRect(ctx, IMG_X, MARGIN, iw, ih, 9)
  ctx.stroke()

  ctx.font = '500 13px "IBM Plex Mono", ui-monospace, monospace'
  ctx.fillStyle = 'rgba(206,201,184,0.8)'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(`→ ${String(index + 1).padStart(2, '0')}`, SLOT * 2, H - MARGIN / 2)
  ctx.fillText(script.mark, SLOT * 6, H - MARGIN / 2)

  ctx.globalCompositeOperation = 'destination-out'
  ctx.fillStyle = '#000'
  for (let k = 0; k < 8; k += 1) {
    const x = k * SLOT + (SLOT - HOLE_W) / 2
    roundRect(ctx, x, (MARGIN - HOLE_H) / 2, HOLE_W, HOLE_H, 5)
    ctx.fill()
    roundRect(ctx, x, H - MARGIN + (MARGIN - HOLE_H) / 2, HOLE_W, HOLE_H, 5)
    ctx.fill()
  }
  ctx.globalCompositeOperation = 'source-over'
}

function roundRect(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, radius)
}

function paintCode(
  ctx: CanvasRenderingContext2D,
  script: FilmScript,
  x: number,
  y: number,
  width: number,
  height: number,
) {
  const lineFactor = 1.36
  const fit = Math.floor((height * 0.88) / (script.lines.length * lineFactor))
  const fontSize = Math.max(9, Math.min(Math.round(height * 0.05), fit))
  const keywords = new Set(script.keywords)
  ctx.font = `400 ${fontSize}px "IBM Plex Mono", ui-monospace, monospace`
  ctx.textBaseline = 'top'
  ctx.textAlign = 'left'
  const lineH = fontSize * lineFactor
  let cursorY = y + Math.max(fontSize * 0.8, (height - script.lines.length * lineH) / 2)
  const cursorX = x + fontSize * 1.4
  const maxX = x + width - fontSize
  ctx.shadowBlur = 4
  for (const line of script.lines) {
    let cursor = cursorX
    for (const token of tokenize(line, keywords)) {
      if (cursor > maxX) break
      ctx.fillStyle = INK[token.kind]
      ctx.shadowColor = `${INK[token.kind]}88`
      ctx.fillText(token.text, cursor, cursorY)
      cursor += ctx.measureText(token.text).width
    }
    cursorY += lineH
  }
  ctx.shadowBlur = 0
}

function tokenize(line: string, keywords: ReadonlySet<string>) {
  const trimmed = line.trimStart()
  if (trimmed.startsWith('//') || trimmed.startsWith('#') || trimmed.startsWith('--')) {
    return [{ text: line, kind: 'comment' as const }]
  }

  const tokens: { text: string; kind: InkKind }[] = []
  let i = 0
  while (i < line.length) {
    const ch = line[i] ?? ''
    if (ch === '"' || ch === "'" || ch === '`') {
      let j = i + 1
      while (j < line.length && line[j] !== ch) j += 1
      j = Math.min(line.length, j + 1)
      tokens.push({ text: line.slice(i, j), kind: 'string' })
      i = j
      continue
    }
    if (ch >= '0' && ch <= '9') {
      let j = i + 1
      while (j < line.length && /[0-9.]/.test(line[j] ?? '')) j += 1
      tokens.push({ text: line.slice(i, j), kind: 'number' })
      i = j
      continue
    }
    if (/[A-Za-z_Ѐ-ӿ]/.test(ch)) {
      let j = i + 1
      while (j < line.length && /[A-Za-z0-9_Ѐ-ӿ]/.test(line[j] ?? '')) j += 1
      const word = line.slice(i, j)
      tokens.push({ text: word, kind: keywords.has(word) ? 'keyword' : 'text' })
      i = j
      continue
    }
    tokens.push({ text: ch, kind: 'text' })
    i += 1
  }
  return tokens
}

// Scratches run along the strip and sit at the same height in every row, so they stay continuous
function paintWear(ctx: CanvasRenderingContext2D, W: number, H: number, rnd: () => number) {
  ctx.globalCompositeOperation = 'source-atop'
  for (let i = 0; i < 7; i += 1) {
    const v = 0.2 + rnd() * 0.6
    const alpha = 0.035 + rnd() * 0.06
    for (let row = 0; row < ROWS; row += 1) {
      const y = row * CELL_H + v * CELL_H
      let x = rnd() * W * 0.3
      while (x < W) {
        const len = 200 + rnd() * 1400
        ctx.strokeStyle = `rgba(220,228,255,${alpha * (0.5 + rnd() * 0.5)})`
        ctx.lineWidth = 0.6 + rnd() * 0.6
        ctx.beginPath()
        ctx.moveTo(x, y)
        ctx.lineTo(Math.min(W, x + len), y + (rnd() - 0.5) * 2)
        ctx.stroke()
        x += len + rnd() * 900
      }
    }
  }
  for (let i = 0; i < 280; i += 1) {
    const dark = rnd() < 0.75
    ctx.fillStyle = dark
      ? `rgba(0,0,0,${0.35 + rnd() * 0.4})`
      : `rgba(230,235,255,${0.1 + rnd() * 0.14})`
    ctx.beginPath()
    ctx.arc(rnd() * W, rnd() * H, 0.6 + rnd() * 1.5, 0, Math.PI * 2)
    ctx.fill()
  }
  for (let i = 0; i < 5; i += 1) {
    const x = rnd() * W
    const y = rnd() * H
    ctx.strokeStyle = 'rgba(0,0,0,0.45)'
    ctx.lineWidth = 0.8
    ctx.beginPath()
    ctx.moveTo(x, y)
    ctx.bezierCurveTo(
      x + 20 + rnd() * 30,
      y - 20 + rnd() * 40,
      x + 30 + rnd() * 40,
      y - 30 + rnd() * 60,
      x + 50 + rnd() * 50,
      y - 10 + rnd() * 20,
    )
    ctx.stroke()
  }
  ctx.globalCompositeOperation = 'source-over'
}
