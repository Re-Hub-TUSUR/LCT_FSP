import { useEffect, useRef } from 'react'
import './film-glitch.css'

type Props = {
  poster: string
}

type Kind = 'text' | 'keyword' | 'string' | 'comment' | 'number'

type Script = {
  mark: string
  keywords: readonly string[]
  lines: readonly string[]
}

const VERT = `
attribute vec2 aPos;
varying vec2 vUv;
void main() {
  vUv = aPos * 0.5 + 0.5;
  gl_Position = vec4(aPos, 0.0, 1.0);
}
`

const FRAG = `
precision mediump float;
uniform sampler2D uTex;
uniform float uTime;
varying vec2 vUv;
void main() {
  vec2 uv = vec2(vUv.x, 1.0 - vUv.y);
  float wave = sin(uv.x * 6.28318 * 1.05 + uTime * 0.7);
  float harmonic = sin(uv.x * 6.28318 * 2.2 - uTime * 1.15);
  uv.y += wave * 0.045 + harmonic * 0.012;
  float burst = smoothstep(0.9, 0.99, sin(uTime * 6.28318 / 5.0));
  float band = step(0.82, fract(uv.y * 16.0 + uTime));
  uv.x += burst * band * 0.02;
  float split = 0.0015 + burst * 0.006;
  float r = texture2D(uTex, uv + vec2(split, 0.0)).r;
  float g = texture2D(uTex, uv).g;
  float b = texture2D(uTex, uv - vec2(split, 0.0)).b;
  gl_FragColor = vec4(r, g, b, 1.0);
}
`

const INK: Record<Kind, string> = {
  text: '#e7e9f2',
  keyword: '#9aabff',
  string: '#f0a3ad',
  comment: '#7e879f',
  number: '#e4d2a4',
}

const SCRIPTS: readonly Script[] = [
  {
    mark: 'TS',
    keywords: ['type', 'function', 'const', 'if', 'return'],
    lines: [
      'type Candidate = {',
      '  email: string',
      '  skills: string[]',
      '}',
      '',
      'function invite(person: Candidate) {',
      '  const score = rank(person.skills)',
      '  if (score < 80) return null',
      '  return {',
      '    to: person.email,',
      '    when: nextSlot(),',
      '  }',
      '}',
      '',
      'function rank(skills: string[]) {',
      '  const known = ["go", "rust", "sql"]',
      '  const hit = skills.filter((s) =>',
      '    known.includes(s),',
      '  )',
      '  return hit.length / known.length',
      '}',
    ],
  },
  {
    mark: 'Q',
    keywords: ['Вопрос'],
    lines: [
      'Вопрос',
      '',
      'Как устроен планировщик в Go',
      'и чем горутина отличается',
      'от потока операционной системы?',
      '',
      'Ждём модель GMP: кто держит',
      'поток, когда горутина его',
      'отдаёт и что происходит',
      'на блокирующем syscall.',
      '',
      'Плюс: зачем нужен GOMAXPROCS',
      'и как поймать голодание.',
    ],
  },
  {
    mark: 'VAC',
    keywords: ['Вакансия', 'Стек', 'Формат'],
    lines: [
      'Вакансия',
      '',
      'Backend, Go',
      'Формат: удалённо, middle+',
      '',
      'Держать сервис найма:',
      'очереди писем, права,',
      'слоты календаря.',
      '',
      'Стек: Go, Postgres, Redis.',
      'Нужен человек, который',
      'читает план запроса и',
      'не боится чужой схемы.',
    ],
  },
  {
    mark: 'PY',
    keywords: ['def', 'return', 'if', 'for', 'in'],
    lines: [
      'def rank(skills: list[str]) -> float:',
      '    known = {"go", "rust", "sql"}',
      '    hit = known.intersection(skills)',
      '    if not hit:',
      '        return 0.0',
      '    return len(hit) / len(known)',
      '',
      'def shortlist(people, floor=0.6):',
      '    ready = []',
      '    for person in people:',
      '        score = rank(person.skills)',
      '        if score >= floor:',
      '            ready.append(person)',
      '    return ready',
    ],
  },
  {
    mark: 'Q',
    keywords: ['Вопрос'],
    lines: [
      'Вопрос',
      '',
      'Когда btree-индекс в Postgres',
      'перестаёт помогать запросу?',
      '',
      'Разберите план: Seq Scan',
      'против Index Scan, rows,',
      'cost и buffers.',
      '',
      'Что будет, если условие',
      'отсекает слишком мало строк,',
      'и зачем тут частичный индекс.',
    ],
  },
  {
    mark: 'VAC',
    keywords: ['Вакансия', 'Стек', 'Формат'],
    lines: [
      'Вакансия',
      '',
      'Frontend, React',
      'Формат: удалённо, middle',
      '',
      'Собрать кабинет найма:',
      'лента кандидатов,',
      'приглашения, календарь.',
      '',
      'Стек: React, TypeScript.',
      'Важны пустые состояния,',
      'клавиатура и то, как',
      'интерфейс ведёт себя',
      'на узком экране.',
    ],
  },
  {
    mark: 'GO',
    keywords: ['func', 'for', 'if', 'return', 'range', 'type'],
    lines: [
      'type Day struct {',
      '    At   time.Time',
      '    Open bool',
      '}',
      '',
      'func NextSlot(days []Day) time.Time {',
      '    for _, day := range days {',
      '        if day.Open {',
      '            return day.At',
      '        }',
      '    }',
      '    return time.Now()',
      '}',
      '',
      'func Open(days []Day) int {',
      '    n := 0',
      '    for _, day := range days {',
      '        if day.Open {',
      '            n++',
      '        }',
      '    }',
      '    return n',
      '}',
    ],
  },
  {
    mark: 'Q',
    keywords: ['Вопрос'],
    lines: [
      'Вопрос',
      '',
      'Два запроса пишут один',
      'баланс. Как не потерять',
      'деньги без лишних блокировок?',
      '',
      'Сравните транзакцию,',
      'оптимистичную версию',
      'и очередь команд.',
      '',
      'Где будет гонка, если',
      'читать баланс в приложении',
      'и писать его обратно.',
    ],
  },
  {
    mark: 'VAC',
    keywords: ['Вакансия', 'Стек', 'Формат'],
    lines: [
      'Вакансия',
      '',
      'Данные, SQL',
      'Формат: гибрид, middle+',
      '',
      'Считать качество найма:',
      'отклик, приглашение,',
      'слот, выход.',
      '',
      'Стек: SQL, Python.',
      'Нужны честные витрины,',
      'а не дашборд ради',
      'красивой цифры.',
    ],
  },
  {
    mark: 'RS',
    keywords: ['fn', 'if', 'return', 'struct', 'impl'],
    lines: [
      'struct Score(u8);',
      '',
      'impl Score {',
      '    fn accept(&self) -> bool {',
      '        self.0 >= 80',
      '    }',
      '}',
      '',
      'fn decide(score: Score) -> &str {',
      '    if score.accept() {',
      '        return "invite";',
      '    }',
      '    "wait"',
      '}',
    ],
  },
  {
    mark: 'Q',
    keywords: ['Вопрос'],
    lines: [
      'Вопрос',
      '',
      'Спроектируйте ленту,',
      'где компания листает',
      'карточки, а кандидат',
      'видит только приглашение.',
      '',
      'Где хранить жест,',
      'как не показать одну',
      'карточку дважды и что',
      'делать, если лента',
      'закончилась посреди сессии.',
    ],
  },
  {
    mark: 'VAC',
    keywords: ['Вакансия', 'Стек', 'Формат'],
    lines: [
      'Вакансия',
      '',
      'Платформа, SRE',
      'Формат: удалённо, senior',
      '',
      'Держать вход в сервис:',
      'письма, очереди, входы.',
      '',
      'Стек: Linux, Postgres,',
      'наблюдаемость.',
      'Нужен человек, который',
      'сначала смотрит график,',
      'потом трогает конфиг.',
    ],
  },
  {
    mark: 'SQL',
    keywords: ['select', 'from', 'where', 'order', 'by', 'limit', 'and', 'join', 'on'],
    lines: [
      'select s.name, s.grade',
      'from specialists s',
      'join skills k',
      '  on k.person_id = s.id',
      "where k.name = 'rust'",
      '  and s.grade >= 80',
      '  and s.open = true',
      'order by s.grade desc,',
      '  s.updated_at desc',
      'limit 12;',
    ],
  },
  {
    mark: 'Q',
    keywords: ['Вопрос'],
    lines: [
      'Вопрос',
      '',
      'Есть массив слотов.',
      'Нужен ближайший свободный',
      'после заданного часа.',
      '',
      'Какая сложность у линейного',
      'прохода и когда имеет смысл',
      'дерево по времени.',
      '',
      'Что сломается, если слоты',
      'приходят не по порядку',
      'и часть из них уже прошла.',
    ],
  },
  {
    mark: 'CS',
    keywords: ['async', 'var', 'await', 'return', 'new', 'if'],
    lines: [
      'async Task<Invite> Send(User user) {',
      '    var code = Codes.Next();',
      '    var sent = await mail.Send(',
      '        user.Email,',
      '        code',
      '    );',
      '    if (!sent) {',
      '        throw new MailDown();',
      '    }',
      '    return new Invite(user.Id, code);',
      '}',
    ],
  },
  {
    mark: 'VAC',
    keywords: ['Вакансия', 'Стек', 'Формат'],
    lines: [
      'Вакансия',
      '',
      'Мобильная разработка',
      'Формат: офис или гибрид',
      '',
      'Карточка кандидата',
      'и ответ на приглашение',
      'с телефона, без лишних',
      'шагов.',
      '',
      'Стек: Kotlin или Swift.',
      'Нужен спокойный интерфейс',
      'и уважение к жесту.',
    ],
  },
]

/**
 * A looping film strip of code stills. The strip bends on a sine wave.
 * Previous look is kept in film-glitch.wave.bak.
 */
export function FilmGlitch(_props: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const parent = canvas?.parentElement
    if (!canvas || !parent) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const gl = canvas.getContext('webgl', { alpha: false, antialias: false })
    if (!gl) return
    const program = createProgram(gl)
    if (!program) return

    const scene = document.createElement('canvas')
    const sceneCtx = scene.getContext('2d', { alpha: false })
    if (!sceneCtx) return

    const buffer = gl.createBuffer()
    gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array([-1, -1, 1, -1, -1, 1, 1, 1]), gl.STATIC_DRAW)
    const pos = gl.getAttribLocation(program, 'aPos')
    gl.enableVertexAttribArray(pos)
    gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0)

    const texture = gl.createTexture()
    gl.bindTexture(gl.TEXTURE_2D, texture)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)

    const bindProgram = gl.useProgram.bind(gl)
    bindProgram(program)
    const timeLoc = gl.getUniformLocation(program, 'uTime')

    let slides: HTMLCanvasElement[] = []
    let slideKey = ''
    let frame = 0
    let running = true
    let onScreen = false
    const started = performance.now()

    const rebuild = (width: number, height: number) => {
      const frameH = Math.max(1, Math.round(height * 0.72))
      const cssWidth = parent.clientWidth || 1
      const basis = Math.round(width * Math.min(1, (window.innerWidth || cssWidth) / cssWidth))
      const frameW = Math.max(1, Math.round(Math.min(basis * 0.62, frameH * 1.55)))
      const next = `${frameW}x${frameH}`
      if (next === slideKey) return
      slideKey = next
      slides = SCRIPTS.map((script, index) => paintFrame(script, frameW, frameH, index))
    }

    const draw = (now: number) => {
      if (!running || !onScreen) return
      const time = (now - started) / 1000
      const { width, height } = sizeToParent(canvas, parent)
      if (scene.width !== width || scene.height !== height) {
        scene.width = width
        scene.height = height
      }
      rebuild(width, height)
      paintStrip(sceneCtx, slides, time, filmScrollShift(slides[0]?.width ?? 0))
      gl.viewport(0, 0, width, height)
      bindProgram(program)
      gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
      gl.enableVertexAttribArray(pos)
      gl.vertexAttribPointer(pos, 2, gl.FLOAT, false, 0, 0)
      gl.bindTexture(gl.TEXTURE_2D, texture)
      gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, scene)
      gl.uniform1f(timeLoc, time)
      gl.drawArrays(gl.TRIANGLE_STRIP, 0, 4)
      frame = requestAnimationFrame(draw)
    }

    const kick = () => {
      if (!running || !onScreen) return
      cancelAnimationFrame(frame)
      frame = requestAnimationFrame(draw)
    }

    const watch = parent.closest('.chapter, .hero') ?? parent
    const box = watch.getBoundingClientRect()
    onScreen = box.bottom > 0 && box.top < window.innerHeight
    kick()

    const resizeObserver = new ResizeObserver(() => sizeToParent(canvas, parent))
    resizeObserver.observe(parent)
    const visibility = new IntersectionObserver(
      (entries) => {
        const entry = entries[0]
        if (!entry) return
        const next = entry.isIntersecting
        if (next === onScreen) return
        onScreen = next
        kick()
      },
      { rootMargin: '25% 0px' },
    )
    visibility.observe(watch)
    void document.fonts?.ready.then(() => {
      slideKey = ''
    })

    return () => {
      running = false
      cancelAnimationFrame(frame)
      resizeObserver.disconnect()
      visibility.disconnect()
    }
  }, [])

  return <canvas ref={canvasRef} className="film-glitch" aria-hidden="true" />
}

function sizeToParent(canvas: HTMLCanvasElement, parent: HTMLElement) {
  const dpr = Math.min(window.devicePixelRatio || 1, 1.5)
  const width = Math.max(1, Math.floor(parent.clientWidth * dpr))
  const height = Math.max(1, Math.floor(parent.clientHeight * dpr))
  if (canvas.width !== width || canvas.height !== height) {
    canvas.width = width
    canvas.height = height
  }
  return { width, height }
}

function createProgram(gl: WebGLRenderingContext) {
  const vert = compile(gl, gl.VERTEX_SHADER, VERT)
  const frag = compile(gl, gl.FRAGMENT_SHADER, FRAG)
  if (!vert || !frag) return null
  const program = gl.createProgram()
  if (!program) return null
  gl.attachShader(program, vert)
  gl.attachShader(program, frag)
  gl.linkProgram(program)
  if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return null
  return program
}

function compile(gl: WebGLRenderingContext, type: number, source: string) {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return null
  return shader
}

function paintFrame(script: Script, width: number, height: number, index: number) {
  const canvas = document.createElement('canvas')
  canvas.width = width
  canvas.height = height
  const ctx = canvas.getContext('2d')
  if (!ctx) return canvas

  ctx.fillStyle = '#161a22'
  ctx.fillRect(0, 0, width, height)
  paintSprockets(ctx, width, height)

  const marginY = Math.round(height * 0.12)
  const padX = Math.round(width * 0.04)
  ctx.fillStyle = '#0b0e16'
  ctx.fillRect(padX, marginY, width - padX * 2, height - marginY * 2)

  ctx.save()
  ctx.beginPath()
  ctx.rect(padX, marginY, width - padX * 2, height - marginY * 2)
  ctx.clip()
  paintCode(ctx, script, padX, marginY, width - padX * 2, height - marginY * 2)
  ctx.restore()

  const label = Math.max(11, Math.round(height * 0.03))
  ctx.font = `400 ${label}px "JetBrains Mono", ui-monospace, monospace`
  ctx.fillStyle = '#c5c9d4'
  ctx.textBaseline = 'middle'
  ctx.textAlign = 'center'
  const no = String(index + 1).padStart(2, '0')
  ctx.fillText(`→ ${no}`, sprocketGapCenter(width, 2), height - marginY / 2)
  ctx.fillText(script.mark, sprocketGapCenter(width, 6), height - marginY / 2)
  ctx.textAlign = 'left'
  return canvas
}

const HOLE_COUNT = 8

function sprocketMetrics(width: number) {
  const holeW = Math.round(width * 0.034)
  const gap = (width - HOLE_COUNT * holeW) / (HOLE_COUNT + 1)
  return { holeW, gap }
}

function sprocketGapCenter(width: number, afterHole: number) {
  const { holeW, gap } = sprocketMetrics(width)
  return gap + afterHole * (holeW + gap) + holeW + gap / 2
}

function paintSprockets(ctx: CanvasRenderingContext2D, width: number, height: number) {
  const marginY = Math.round(height * 0.12)
  const { holeW, gap } = sprocketMetrics(width)
  const holeH = Math.round(marginY * 0.4)
  const radius = Math.max(2, Math.round(holeH * 0.22))
  ctx.fillStyle = '#f4f5f8'
  for (let i = 0; i < HOLE_COUNT; i += 1) {
    const x = gap + i * (holeW + gap)
    const y = (marginY - holeH) / 2
    hole(ctx, x, y, holeW, holeH, radius)
    hole(ctx, x, height - marginY + (marginY - holeH) / 2, holeW, holeH, radius)
  }
}

function hole(
  ctx: CanvasRenderingContext2D,
  x: number,
  y: number,
  w: number,
  h: number,
  radius: number,
) {
  ctx.beginPath()
  ctx.roundRect(x, y, w, h, radius)
  ctx.fill()
}

function paintCode(
  ctx: CanvasRenderingContext2D,
  script: Script,
  x: number,
  y: number,
  width: number,
  height: number,
) {
  const lineFactor = 1.34
  const fit = Math.floor((height * 0.9) / (script.lines.length * lineFactor))
  const fontSize = Math.max(12, Math.min(Math.round(height * 0.055), fit))
  const keywords = new Set(script.keywords)
  ctx.font = `400 ${fontSize}px "JetBrains Mono", ui-monospace, monospace`
  ctx.textBaseline = 'top'
  const lineH = fontSize * lineFactor
  const block = script.lines.length * lineH
  let cursorY = y + Math.max(fontSize * 0.7, (height - block) / 2)
  const cursorX = x + fontSize * 0.7
  for (const line of script.lines) {
    drawLine(ctx, line, cursorX, cursorY, keywords, cursorX + width - fontSize)
    cursorY += lineH
  }
}

function drawLine(
  ctx: CanvasRenderingContext2D,
  line: string,
  x: number,
  y: number,
  keywords: ReadonlySet<string>,
  maxX: number,
) {
  let cursor = x
  for (const token of tokenize(line, keywords)) {
    if (cursor > maxX) return
    ctx.fillStyle = INK[token.kind]
    ctx.fillText(token.text, cursor, y)
    cursor += ctx.measureText(token.text).width
  }
}

function tokenize(line: string, keywords: ReadonlySet<string>) {
  const trimmed = line.trimStart()
  if (trimmed.startsWith('//') || trimmed.startsWith('#') || trimmed.startsWith('--')) {
    return [{ text: line, kind: 'comment' as const }]
  }

  const tokens: { text: string; kind: Kind }[] = []
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
    if (/[A-Za-z_\u0400-\u04FF]/.test(ch)) {
      let j = i + 1
      while (j < line.length && /[A-Za-z0-9_\u0400-\u04FF]/.test(line[j] ?? '')) j += 1
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

const FRAMES_PER_SECTION = 4

function filmScrollShift(span: number) {
  if (!span) return 0
  const section = window.innerHeight || 1
  const progress = window.scrollY / section
  const leg = Math.floor(progress)
  const along = progress - leg
  const pullingLeft = leg % 2 === 0
  const amount = pullingLeft ? along : 1 - along
  return amount * FRAMES_PER_SECTION * span
}

function paintStrip(
  ctx: CanvasRenderingContext2D,
  slides: HTMLCanvasElement[],
  time: number,
  scrollShift: number,
) {
  const { width, height } = ctx.canvas
  ctx.fillStyle = '#05071a'
  ctx.fillRect(0, 0, width, height)
  const first = slides[0]
  if (!first) return
  const span = first.width
  const count = slides.length
  const cycle = span * count
  const travel = (((time * span * 0.12 + scrollShift) % cycle) + cycle) % cycle
  const y = (height - first.height) / 2

  for (let index = 0; index < count; index += 1) {
    const slide = slides[index]
    if (!slide) continue
    const base = index * span - travel
    drawFrame(ctx, slide, base, y, width)
    drawFrame(ctx, slide, base + count * span, y, width)
  }
}

function drawFrame(
  ctx: CanvasRenderingContext2D,
  slide: HTMLCanvasElement,
  x: number,
  y: number,
  width: number,
) {
  if (x >= width || x + slide.width <= 0) return
  ctx.drawImage(slide, x, y)
}
