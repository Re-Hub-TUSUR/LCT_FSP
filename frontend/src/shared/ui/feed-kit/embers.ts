import { fxPixelRatio } from './film-fx'

type Ember = {
  x: number
  y: number
  vx: number
  vy: number
  life: number
  max: number
  r: number
  phase: number
}

const LIMIT = 420

/** Sparks flying off the burning edge: particles on a 2D canvas over the whole gate. */
export class FilmEmbers {
  private readonly ctx: CanvasRenderingContext2D | null
  private embers: Ember[] = []

  constructor(private readonly canvas: HTMLCanvasElement) {
    // jsdom has no canvas: the reel simply burns without sparks.
    this.ctx = typeof CanvasRenderingContext2D === 'undefined' ? null : canvas.getContext('2d')
  }

  /** `drift` pushes the sparks sideways, away from where the fire goes. */
  spawn(x: number, y: number, drift: number) {
    if (!this.ctx) return
    this.embers.push({
      x: x + (Math.random() - 0.5) * 6,
      y: y + (Math.random() - 0.5) * 6,
      vx: (Math.random() - 0.5) * 50 + drift * (10 + Math.random() * 40),
      vy: -(25 + Math.random() * 95),
      life: 0,
      max: 0.55 + Math.random() * 1.1,
      r: 0.6 + Math.random() * 1.7,
      phase: Math.random() * 6.28,
    })
    if (this.embers.length > LIMIT) this.embers.splice(0, this.embers.length - LIMIT)
  }

  get alive() {
    return this.embers.length > 0
  }

  /** Drops the current burst and clears the last painted frame. */
  clear() {
    this.embers = []
    const { ctx, canvas } = this
    if (!ctx) return
    ctx.setTransform(1, 0, 0, 1, 0, 0)
    ctx.globalCompositeOperation = 'source-over'
    ctx.clearRect(0, 0, canvas.width, canvas.height)
  }

  /** Moves and repaints every spark; `dt` is in seconds. */
  step(dt: number) {
    const { ctx, canvas } = this
    if (!ctx) return
    const ratio = fxPixelRatio()
    const width = Math.round(canvas.clientWidth * ratio)
    const height = Math.round(canvas.clientHeight * ratio)
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width
      canvas.height = height
    }
    ctx.setTransform(ratio, 0, 0, ratio, 0, 0)
    ctx.clearRect(0, 0, width, height)
    ctx.globalCompositeOperation = 'lighter'

    const next: Ember[] = []
    for (const ember of this.embers) {
      ember.life += dt
      if (ember.life >= ember.max) continue
      // Hot air lifts the spark, turbulence shakes it sideways.
      ember.vy -= 55 * dt
      ember.vx += (Math.random() - 0.5) * 160 * dt
      ember.vx *= 1 - 0.8 * dt
      ember.x += ember.vx * dt
      ember.y += ember.vy * dt

      // Yellow-white → orange → red as it cools down.
      const age = ember.life / ember.max
      const flicker = 0.65 + 0.35 * Math.sin(ember.life * 22 + ember.phase)
      const alpha = (1 - age) * flicker
      const green = Math.round(235 - 170 * age)
      const blue = Math.round(150 * Math.max(0, 1 - age * 3))
      ctx.fillStyle = `rgba(255,${green},${blue},${alpha * 0.22})`
      ctx.beginPath()
      ctx.arc(ember.x, ember.y, ember.r * 3.2, 0, 6.283)
      ctx.fill()
      ctx.fillStyle = `rgba(255,${Math.min(255, green + 20)},${blue + 40},${alpha})`
      ctx.beginPath()
      ctx.arc(ember.x, ember.y, ember.r, 0, 6.283)
      ctx.fill()
      next.push(ember)
    }
    this.embers = next
  }
}
