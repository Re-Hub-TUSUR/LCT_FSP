import { layoutMark, paintMark } from './editor-mark'
import type { MarkGeometry, MarkParts } from './editor-mark'
import { FilmEmbers } from './embers'
import { FilmFX } from './film-fx'

export type SwipeDecision = 'like' | 'skip'

/** One action button: the coloured ring grows and glows as the swipe goes its way. */
type ActButton = { button: HTMLButtonElement; ring: HTMLElement; icon: HTMLElement }

/** DOM the engine writes to every frame. Anything may be missing while the deck is empty. */
export type ReelElements = {
  gate: HTMLElement | null
  track: HTMLElement | null
  /** The window of the current frame: it tilts with the drag. */
  window: HTMLElement | null
  /** The card inside it: heat, development and the pencil's pressure are filters on it. */
  card: HTMLElement | null
  grain: HTMLElement | null
  fx: HTMLCanvasElement | null
  embers: HTMLCanvasElement | null
  mark: MarkParts | null
  skip: ActButton | null
  like: ActButton | null
}

/** How the engine reaches the deck: its DOM and what to tell it. */
export type ReelHost = {
  /** Read on every frame: the elements change as cards come and go. */
  elements: () => ReelElements
  /** Buttons are disabled while a decision plays out. */
  onBusy: (busy: boolean) => void
  /** The animation is over: the deck must show the next card now. */
  onDecide: (decision: SwipeDecision) => void
}

/** Everything painted in one frame; the rest state is "nothing is happening". */
type Visual = {
  burning: boolean
  front: number
  origin: readonly [number, number]
  heat: number
  tilt: number
  lift: number
  skipK: number
  likeK: number
  mark: number
  tick: number
  press: number
}

const REST: Visual = {
  burning: false,
  front: -1,
  origin: [0, 0.5],
  heat: 0,
  tilt: 0,
  lift: 0,
  skipK: 0,
  likeK: 0,
  mark: 0,
  tick: 0,
  press: 0,
}

type Drag = {
  pointer: number
  x0: number
  y0: number
  offset0: number
  /** Past the 6px dead zone and recognised as horizontal. */
  active: boolean
  /** The threshold is crossed: the haptic tick has been given. */
  armed: boolean
  samples: { x: number; t: number }[]
}

type Animation = {
  decision: SwipeDecision
  t0: number
  /** Values the commit starts from, so the preview continues without a jump. */
  offset0: number
  origin: readonly [number, number]
  front0: number
  heat0: number
  tilt0: number
  lift0: number
  mark0: number
  ticked: boolean
}

const MOBILE_WIDTH = 720
/** Share of the gate one frame takes; the stylesheet sizes the track to match. */
const FRAME_SHARE = { desktop: 0.75, mobile: 0.86 }
const DRAG_START = 6
/** Share of the threshold after which a drag starts to preview its decision on the frame. */
const PREVIEW_FROM = 0.8
const DEVELOP_MS = 720
const SPRING = 300

const clamp = (value: number, min = 0, max = 1) => Math.min(max, Math.max(min, value))
const lerp = (from: number, to: number, t: number) => from + (to - from) * t
const easeOut = (t: number) => 1 - (1 - t) ** 3
const easeInOut = (t: number) => (t < 0.5 ? 4 * t * t * t : 1 - (-2 * t + 2) ** 3 / 2)
const smooth = (t: number) => t * t * (3 - 2 * t)

function buzz(ms: number) {
  try {
    navigator.vibrate?.(ms)
  } catch {
    // Haptics are a nicety; some browsers throw outside a user gesture.
  }
}

/**
 * The swipe reel between two React renders.
 *
 * React owns only what changes the markup (which card is current, whether the buttons are
 * disabled). Everything that moves — the strip, the fire, the pencil, the development of a new
 * frame — lives here and is written straight to the DOM from one requestAnimationFrame loop,
 * which runs only while something is in motion.
 */
export class ReelEngine {
  private hover: SwipeDecision | null = null
  private offset = 0
  private springVelocity = 0
  private spring = false
  private visual: Visual = REST
  /** 1 = an undeveloped frame, 0 = a clean one. */
  private development = 0
  private developStart: number | null = null
  private drag: Drag | null = null
  private dragProgress = 0
  /** Vertical grab point, 0 (bottom) to 1 (top): where the fire starts. */
  private grabY = 0.5
  private animation: Animation | null = null
  /** The decision is made, React has not shown the next card yet: nothing may be painted. */
  private pending = false
  private busy = false
  private emberDebt = 0
  private frame = 0
  private lastTime = 0
  private time = 0
  private fx: FilmFX | null = null
  private fxCanvas: HTMLCanvasElement | null = null
  private embers: FilmEmbers | null = null
  private embersCanvas: HTMLCanvasElement | null = null
  private markGeometry: MarkGeometry | null = null

  constructor(private readonly host: ReelHost) {}

  private elements() {
    return this.host.elements()
  }

  /** The mouse is over a button (or left it): its ring grows a little. */
  setHover(decision: SwipeDecision | null) {
    this.hover = decision
    this.apply()
  }

  // ── Geometry ──────────────────────────────────────────────────────────────────────────

  private mobile() {
    return window.innerWidth <= MOBILE_WIDTH
  }

  private geometry() {
    const width = this.elements().gate?.clientWidth || 1
    const share = this.mobile() ? FRAME_SHARE.mobile : FRAME_SHARE.desktop
    // Five cells; at rest the middle one is centred in the gate.
    return { width, cell: width * share, rest: width * (0.5 - 2.5 * share) }
  }

  private threshold() {
    const { width } = this.geometry()
    return this.mobile() ? Math.max(64, width * 0.2) : clamp(width * 0.08, 96, 140)
  }

  private reducedMotion() {
    return window.matchMedia?.('(prefers-reduced-motion: reduce)').matches ?? false
  }

  // ── Loop ──────────────────────────────────────────────────────────────────────────────

  private loop() {
    if (this.frame) return
    this.lastTime = 0
    const step = () => {
      this.frame = 0
      // Not the timestamp of the callback: it may run on another clock than `performance.now()`,
      // which the animations are started with.
      const keep = this.update(performance.now())
      this.apply()
      if (keep && !this.pending) this.frame = requestAnimationFrame(step)
    }
    this.frame = requestAnimationFrame(step)
  }

  /** Advances the state by one frame; false when everything has come to rest. */
  private update(now: number): boolean {
    const dt = this.lastTime ? Math.min(0.05, (now - this.lastTime) / 1000) : 1 / 60
    this.lastTime = now
    this.time = now / 1000
    const visual: Visual = { ...REST }
    let keep = false

    if (this.animation) {
      keep = true
      this.runAnimation(this.animation, now, dt, visual)
    } else {
      if (this.spring) {
        const damping = 2 * Math.sqrt(SPRING) * 0.85
        this.springVelocity += (-SPRING * this.offset - damping * this.springVelocity) * dt
        this.offset += this.springVelocity * dt
        if (Math.abs(this.offset) < 0.4 && Math.abs(this.springVelocity) < 6) {
          this.offset = 0
          this.springVelocity = 0
          this.spring = false
        } else {
          keep = true
        }
      }
      if (this.drag) keep = true
      const progress = this.drag?.active
        ? this.dragProgress
        : clamp(Math.abs(this.offset) / this.threshold())
      const side = Math.sign(this.offset)
      if (progress > 0.001 && side) this.preview(visual, side, progress, dt)
    }

    if (this.developStart !== null) {
      const k = clamp((now - this.developStart) / DEVELOP_MS)
      this.development = 1 - easeOut(k)
      if (k >= 1) {
        this.developStart = null
        this.development = 0
      } else {
        keep = true
      }
    }
    if (this.embers?.alive) {
      this.embers.step(dt)
      keep = true
    }
    this.visual = visual
    return keep
  }

  /** What a drag shows before it is released: the fire licks the edge or the pencil starts. */
  private preview(visual: Visual, side: number, progress: number, dt: number) {
    const eased = smooth(progress)
    visual.tilt = clamp((this.offset / this.geometry().width) * 28, -5, 5)
    visual.lift = 0.012 * progress
    if (side < 0) {
      visual.burning = true
      visual.front = lerp(-0.26, 0.03, eased)
      visual.origin = [-0.04, this.grabY]
      visual.heat = 0.3 * progress
      visual.skipK = progress
      if (progress > 0.55 && this.drag) this.emit(26 * progress * dt, visual.front, visual.origin)
    } else {
      this.ensureMark()
      // The fire only shows past ~80% of the threshold (its front starts behind the edge); the
      // pencil waits as long, so both sides answer the drag alike.
      visual.mark = 0.26 * smooth(clamp((progress - PREVIEW_FROM) / (1 - PREVIEW_FROM)))
      visual.likeK = progress
    }
  }

  /** The timelines of the two decisions, in milliseconds from the commit. */
  private runAnimation(animation: Animation, now: number, dt: number, visual: Visual) {
    const t = now - animation.t0
    const { width, cell } = this.geometry()
    let done: boolean

    if (animation.decision === 'skip') {
      const BURN = 1050
      const HOLD = 600
      const TRANSPORT = 740
      visual.burning = true
      visual.origin = animation.origin
      // The fire flares up: slow at first, then it takes the whole frame.
      visual.front = lerp(animation.front0, 1.45, clamp(t / BURN) ** 1.5)
      visual.heat = lerp(animation.heat0, 1, easeOut(clamp(t / 420)))
      visual.skipK = Math.max(0, 1 - t / 900)
      if (visual.front > 0 && visual.front < 1.35) this.emit(95 * dt, visual.front, visual.origin)
      const hold = Math.min(animation.offset0, -0.03 * width) - 0.012 * width
      this.offset =
        t < HOLD
          ? lerp(animation.offset0, hold, easeOut(clamp(t / HOLD)))
          : lerp(hold, -cell, easeInOut(clamp((t - HOLD) / TRANSPORT)))
      done = t >= HOLD + TRANSPORT
    } else {
      const CIRCLE = 520
      const TICK_AT = CIRCLE + 40
      const TICK = 280
      const HOLD = 1020
      const TRANSPORT = 740
      this.ensureMark()
      visual.mark = lerp(animation.mark0, 1, easeInOut(clamp(t / CIRCLE)))
      visual.tick = clamp((t - TICK_AT) / TICK)
      // The card gives a little under the pencil while the tick is drawn.
      visual.press = Math.sin(Math.PI * clamp((t - TICK_AT) / (TICK + 160))) * 0.6
      if (visual.tick > 0 && !animation.ticked) {
        animation.ticked = true
        buzz(6)
      }
      visual.likeK = Math.max(0, 1 - t / 1000)
      const hold = Math.max(animation.offset0 * 0.4, 0)
      // The mark rides away with the frame.
      this.offset =
        t < HOLD
          ? lerp(animation.offset0, hold, easeOut(clamp(t / HOLD)))
          : lerp(hold, cell, easeInOut(clamp((t - HOLD) / TRANSPORT)))
      done = t >= HOLD + TRANSPORT
    }

    const settle = 1 - easeOut(clamp(t / 340))
    visual.tilt = animation.tilt0 * settle
    visual.lift = animation.lift0 * settle
    if (done) {
      // The card may swap synchronously from `onDecide`; don't let this final burn frame
      // get painted over the newly mounted card after `afterSwap` has reset the engine.
      Object.assign(visual, REST)
      this.swap(animation.decision)
    }
  }

  /** Throws sparks along the estimated edge of the fire. */
  private emit(amount: number, front: number, origin: readonly [number, number]) {
    const { gate, window: frame, embers: canvas } = this.elements()
    if (!gate || !frame || !canvas) return
    if (canvas !== this.embersCanvas) {
      this.embersCanvas = canvas
      this.embers = new FilmEmbers(canvas)
    }
    this.emberDebt += amount
    if (this.emberDebt < 1 || !this.embers) return
    const gateBox = gate.getBoundingClientRect()
    const frameBox = frame.getBoundingClientRect()
    const { width, height } = frameBox
    const aspect = width / height
    const direction = origin[0] < 0.5 ? 1 : -1
    while (this.emberDebt >= 1) {
      this.emberDebt -= 1
      const angle = (Math.random() - 0.5) * Math.PI * 0.9
      const radius =
        Math.max(0, (front - 0.28) / 0.9) * (aspect + 0.6) * height +
        (Math.random() - 0.5) * 0.06 * height
      const x = origin[0] * width + Math.cos(angle) * radius * direction
      const y = (1 - origin[1]) * height - Math.sin(angle) * radius
      if (x < 0 || x > width || y < 0 || y > height) continue
      this.embers.spawn(
        frameBox.left - gateBox.left + x,
        frameBox.top - gateBox.top + y,
        -direction * 0.6,
      )
    }
  }

  // ── Painting ──────────────────────────────────────────────────────────────────────────

  /** Writes the current state to the DOM. Safe to call at any time. */
  apply() {
    if (this.pending) return
    const elements = this.elements()
    const visual = this.visual
    const { rest } = this.geometry()

    if (elements.track) {
      elements.track.style.transform = `translate3d(${(rest + this.offset).toFixed(2)}px,0,0)`
    }
    if (elements.window) {
      elements.window.style.transform =
        visual.tilt || visual.lift
          ? `perspective(1400px) rotateY(${visual.tilt.toFixed(3)}deg) scale(${(1 - visual.lift).toFixed(4)})`
          : ''
    }
    if (elements.card) this.paintCard(elements.card, visual)
    if (elements.grain) {
      elements.grain.style.opacity = String(Math.max(0.4 * this.development, 0.25 * visual.heat))
    }

    if (visual.burning && elements.fx) {
      if (elements.fx !== this.fxCanvas) {
        this.fx?.destroy()
        this.fxCanvas = elements.fx
        this.fx = new FilmFX(elements.fx)
      }
      this.fx?.render({ front: visual.front, origin: visual.origin, time: this.time })
    } else {
      this.fx?.clear()
    }
    if (elements.mark) paintMark(elements.mark, this.markGeometry, visual.mark, visual.tick)

    if (elements.skip) {
      this.paintButton(elements.skip, visual.skipK, this.hover === 'skip', '#ec1d35', '236,29,53')
    }
    if (elements.like) {
      this.paintButton(elements.like, visual.likeK, this.hover === 'like', '#402fff', '64,47,255')
    }
    if (elements.gate) elements.gate.style.cursor = this.drag?.active ? 'grabbing' : ''
  }

  private paintCard(card: HTMLElement, visual: Visual) {
    const filters: string[] = []
    if (this.development > 0) {
      // A new frame develops: blurred, dark and sepia → clean.
      const d = this.development
      filters.push(
        `blur(${(8 * d).toFixed(2)}px)`,
        `brightness(${(1 - 0.45 * d).toFixed(3)})`,
        `sepia(${(0.5 * d).toFixed(3)})`,
      )
      card.style.opacity = String(1 - 0.1 * d)
    } else {
      card.style.opacity = '1'
      if (visual.heat > 0) {
        filters.push(
          `sepia(${(0.7 * visual.heat).toFixed(3)})`,
          `brightness(${(1 - 0.35 * visual.heat).toFixed(3)})`,
          `contrast(${(1 + 0.15 * visual.heat).toFixed(3)})`,
        )
      }
    }
    card.style.filter = filters.length ? filters.join(' ') : 'none'

    // The film shivers in the heat; under the pencil it gives a little instead.
    const shimmer =
      visual.heat > 0.4 && this.animation ? Math.sin(this.time * 47) * 0.6 * visual.heat : 0
    if (shimmer) {
      card.style.transform = `translate3d(${shimmer.toFixed(2)}px,${(shimmer * 0.5).toFixed(2)}px,0)`
    } else {
      card.style.transform = visual.press ? `scale(${(1 - 0.012 * visual.press).toFixed(4)})` : ''
    }
  }

  private paintButton(
    { button, ring, icon }: ActButton,
    k: number,
    hover: boolean,
    color: string,
    rgb: string,
  ) {
    // The button of the decision being played keeps glowing; the other one dims.
    const dimmed = this.busy && !k
    // CSS transitions would lag behind a value that changes every frame.
    const live = Boolean(this.drag?.active || this.animation)
    ring.style.transition = live ? 'none' : ''
    icon.style.transition = live ? 'none' : ''
    const base = dimmed ? 1 : hover ? 1.32 : 1.14
    ring.style.transform = `scale(${(base + 0.34 * k).toFixed(3)})`
    ring.style.opacity = dimmed ? '0.35' : '1'
    if (dimmed) ring.style.boxShadow = 'none'
    else if (hover || k > 0.01) {
      ring.style.boxShadow =
        `0 0 ${(16 + 22 * k).toFixed(1)}px ${color}, ` +
        `0 0 ${(34 + 30 * k).toFixed(1)}px rgba(${rgb},${(0.75 + 0.25 * k).toFixed(2)})`
    } else {
      ring.style.boxShadow = `0 0 14px rgba(${rgb},0.7)`
    }
    icon.style.transform = `scale(${((hover && !dimmed ? 1.06 : 1) + 0.1 * k).toFixed(3)})`
    button.style.opacity = dimmed ? '0.55' : '1'
  }

  private ensureMark() {
    if (this.markGeometry) return
    const { mark, window: frame } = this.elements()
    if (mark && frame) {
      this.markGeometry = layoutMark(mark, frame.clientWidth, frame.clientHeight)
    }
  }

  // ── Decisions ─────────────────────────────────────────────────────────────────────────

  /** Starts a decision from wherever the drag left the frame. */
  commit(decision: SwipeDecision, grabY = 0.5) {
    if (this.animation || this.pending) return
    this.finishDevelopment()
    buzz(12)
    this.drag = null
    this.spring = false
    this.springVelocity = 0
    if (this.reducedMotion()) {
      this.offset = 0
      this.swap(decision)
      return
    }
    const visual = this.visual
    this.animation = {
      decision,
      t0: performance.now(),
      offset0: this.offset,
      origin: [-0.04, grabY],
      front0: visual.burning ? visual.front : -0.26,
      heat0: visual.heat,
      tilt0: visual.tilt,
      lift0: visual.lift,
      mark0: visual.mark,
      ticked: false,
    }
    this.setBusy(true)
    this.loop()
  }

  private setBusy(busy: boolean) {
    if (busy === this.busy) return
    this.busy = busy
    this.host.onBusy(busy)
  }

  /** Hands the decision to React. The burnt frame stays untouched until the next card is in. */
  private swap(decision: SwipeDecision) {
    this.animation = null
    this.pending = true
    this.fx?.clear()
    this.embers?.clear()
    this.emberDebt = 0
    this.setBusy(false)
    this.host.onDecide(decision)
  }

  /**
   * The next card is in the DOM (call before paint): the strip snaps back to rest with the new
   * frame undeveloped, exactly as it looked as a neighbour, and starts to develop.
   */
  afterSwap() {
    this.pending = false
    this.offset = 0
    this.springVelocity = 0
    this.visual = REST
    this.fx?.clear()
    this.embers?.clear()
    this.emberDebt = 0
    this.markGeometry = null
    this.development = 1
    this.developStart = performance.now()
    this.apply()
    this.loop()
  }

  /** The frame changed size: the mark has to be laid out again. */
  resized() {
    this.markGeometry = null
    this.apply()
  }

  private finishDevelopment() {
    if (this.developStart === null) return
    this.developStart = null
    this.development = 0
  }

  // ── Pointer ───────────────────────────────────────────────────────────────────────────

  onPointerDown(event: PointerEvent) {
    if (event.button !== undefined && event.button !== 0) return
    if ((event.target as Element | null)?.closest?.('button, a, dialog')) return
    // Stops text selection and the native image drag before they start.
    event.preventDefault()
    if (this.animation || this.pending) return
    this.finishDevelopment()
    const frame = this.elements().window?.getBoundingClientRect()
    this.drag = {
      pointer: event.pointerId,
      x0: event.clientX,
      y0: event.clientY,
      offset0: this.offset,
      active: false,
      armed: false,
      samples: [{ x: event.clientX, t: performance.now() }],
    }
    this.grabY = frame?.height
      ? clamp(1 - (event.clientY - frame.top) / frame.height, 0.1, 0.9)
      : 0.5
    this.spring = false
    this.springVelocity = 0
  }

  onPointerMove(event: PointerEvent) {
    const drag = this.drag
    if (!drag || event.pointerId !== drag.pointer) return
    const dx = event.clientX - drag.x0
    const dy = event.clientY - drag.y0
    if (!drag.active) {
      if (Math.abs(dx) < DRAG_START && Math.abs(dy) < DRAG_START) return
      // A vertical gesture is a scroll: let it go.
      if (Math.abs(dy) > Math.abs(dx)) {
        this.drag = null
        return
      }
      drag.active = true
      try {
        this.elements().gate?.setPointerCapture?.(event.pointerId)
      } catch {
        // The pointer may be gone already; the drag still works without capture.
      }
    }
    const threshold = this.threshold()
    const raw = drag.offset0 + dx
    const distance = Math.abs(raw)
    // Rubber band: past 1.25 thresholds the frame follows the finger reluctantly.
    const limit = threshold * 1.25
    this.offset = distance <= limit ? raw : Math.sign(raw) * (limit + (distance - limit) * 0.3)
    this.dragProgress = clamp(distance / threshold)
    if (this.dragProgress >= 1 && !drag.armed) {
      drag.armed = true
      buzz(8)
    } else if (this.dragProgress < 0.9) {
      drag.armed = false
    }
    const now = performance.now()
    drag.samples.push({ x: event.clientX, t: now })
    while (drag.samples.length > 2 && now - (drag.samples[0]?.t ?? now) > 120) drag.samples.shift()
    this.loop()
  }

  onPointerUp(event: PointerEvent) {
    const drag = this.drag
    if (!drag || event.pointerId !== drag.pointer) return
    this.drag = null
    if (!drag.active) return
    const first = drag.samples[0]
    const last = drag.samples.at(-1)
    // Pixels per millisecond over the last 120 ms: a quick flick decides too.
    const velocity = first && last && last.t > first.t ? (last.x - first.x) / (last.t - first.t) : 0
    const raw = drag.offset0 + (event.clientX - drag.x0)
    const threshold = this.threshold()
    if (raw <= -threshold || (velocity < -0.5 && raw < -24)) this.commit('skip', this.grabY)
    else if (raw >= threshold || (velocity > 0.5 && raw > 24)) this.commit('like', this.grabY)
    else {
      this.spring = true
      this.springVelocity = velocity * SPRING
      this.loop()
    }
  }

  onPointerCancel() {
    if (!this.drag) return
    this.drag = null
    this.spring = true
    this.loop()
  }

  destroy() {
    cancelAnimationFrame(this.frame)
    this.frame = 0
    this.fx?.destroy()
    this.fx = null
    this.embers?.clear()
    this.embers = null
    this.embersCanvas = null
  }
}
