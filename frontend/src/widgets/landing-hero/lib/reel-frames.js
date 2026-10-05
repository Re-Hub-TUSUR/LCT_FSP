// Draws the 35mm film atlas: 32 frames (code, design, architecture) on 8×4 tiles.
export const S = 512 / 38 // px per mm
export const TW = 512,
  TH = Math.round(35 * S),
  COLS = 8,
  ROWS = 3
const IX = S,
  IY = 5.5 * S,
  IW = 36 * S,
  IH = 24 * S
const PP = 4.75 * S,
  PA = 1.981 * S,
  PX = 2.794 * S,
  PE = 2.01 * S
const SANS = '"IBM Plex Sans", "Helvetica Neue", Arial, sans-serif'
const MONO = '"IBM Plex Mono", "Courier New", monospace'
let c

const P = {
  cream: '#efe4cc',
  paper: '#f4ecdb',
  ink: '#2b211b',
  brown: '#5a3a24',
  orange: '#d9622b',
  mustard: '#e0a83a',
  teal: '#2e8b8b',
  magenta: '#c2457a',
  navy: '#1f2a44',
  sage: '#8fa77a',
  muted: '#a8977c',
  line: '#d9cbb0',
  card: '#fbf5e8',
}

function rng(seed) {
  return () => {
    seed = (seed + 0x6d2b79f5) | 0
    let t = Math.imul(seed ^ (seed >>> 15), 1 | seed)
    t = (t + Math.imul(t ^ (t >>> 7), 61 | t)) ^ t
    return ((t ^ (t >>> 14)) >>> 0) / 4294967296
  }
}
function rr(x, y, w, h, r, fill, stroke, lw = 1, dash) {
  c.beginPath()
  c.roundRect(x, y, w, h, r)
  if (fill) {
    c.fillStyle = fill
    c.fill()
  }
  if (stroke) {
    c.strokeStyle = stroke
    c.lineWidth = lw
    c.setLineDash(dash || [])
    c.stroke()
    c.setLineDash([])
  }
}
function pill(x, y, w, h, col) {
  rr(x, y, w, h, h / 2, col)
}
function circ(x, y, r, fill, stroke, lw = 1) {
  c.beginPath()
  c.arc(x, y, r, 0, Math.PI * 2)
  if (fill) {
    c.fillStyle = fill
    c.fill()
  }
  if (stroke) {
    c.strokeStyle = stroke
    c.lineWidth = lw
    c.stroke()
  }
}
function tri(x1, y1, x2, y2, x3, y3, col) {
  c.beginPath()
  c.moveTo(x1, y1)
  c.lineTo(x2, y2)
  c.lineTo(x3, y3)
  c.closePath()
  c.fillStyle = col
  c.fill()
}
function tx(s, x, y, size, color, o = {}) {
  c.font = `${o.it ? 'italic ' : ''}${o.w || 400} ${size}px ${o.mono ? MONO : SANS}`
  c.fillStyle = color
  c.textAlign = o.al || 'left'
  c.textBaseline = 'alphabetic'
  c.letterSpacing = (o.ls || 0) + 'px'
  c.fillText(s, x, y)
  c.letterSpacing = '0px'
}
function line(pts, col, lw = 1.2, dash) {
  c.beginPath()
  pts.forEach(([x, y], i) => (i ? c.lineTo(x, y) : c.moveTo(x, y)))
  c.strokeStyle = col
  c.lineWidth = lw
  c.lineCap = 'butt'
  c.setLineDash(dash || [])
  c.stroke()
  c.setLineDash([])
}
function head(x, y, a, col, s = 6) {
  tri(
    x,
    y,
    x - s * Math.cos(a - 0.42),
    y - s * Math.sin(a - 0.42),
    x - s * Math.cos(a + 0.42),
    y - s * Math.sin(a + 0.42),
    col,
  )
}
function arrow(pts, col, o = {}) {
  line(pts, col, o.lw || 1.3, o.dash)
  const [x1, y1] = pts[pts.length - 2],
    [x2, y2] = pts[pts.length - 1]
  head(x2, y2, Math.atan2(y2 - y1, x2 - x1), col)
}
function curve(x1, y1, x2, y2, col, o = {}) {
  c.beginPath()
  c.moveTo(x1, y1)
  const mx = (x1 + x2) / 2
  c.bezierCurveTo(mx, y1, mx, y2, x2, y2)
  c.strokeStyle = col
  c.lineWidth = o.lw || 1.3
  c.setLineDash(o.dash || [])
  c.stroke()
  c.setLineDash([])
  if (o.head) head(x2, y2, 0, col)
}

function sunset(x, y, w, h, r) {
  c.save()
  c.beginPath()
  c.roundRect(x, y, w, h, r)
  c.clip()
  const hz = y + h * 0.62,
    cx = x + w / 2,
    sr = Math.min(w, h) * 0.3
  let g = c.createLinearGradient(0, y, 0, hz)
  g.addColorStop(0, '#1d2148')
  g.addColorStop(1, '#8a2f66')
  c.fillStyle = g
  c.fillRect(x, y, w, hz - y)
  g = c.createLinearGradient(0, hz - sr, 0, hz)
  g.addColorStop(0, '#f6c453')
  g.addColorStop(0.55, '#ef7b3b')
  g.addColorStop(1, '#d6407a')
  c.beginPath()
  c.arc(cx, hz, sr, Math.PI, 0)
  c.fillStyle = g
  c.fill()
  for (let i = 0; i < 4; i++) {
    c.fillStyle = '#7c2c63'
    c.fillRect(cx - sr, hz - sr * 0.14 - i * sr * 0.2, sr * 2, 1 + i * 0.9)
  }
  c.fillStyle = '#160f2a'
  c.fillRect(x, hz, w, y + h - hz)
  c.fillStyle = '#f08a5d'
  c.fillRect(x, hz - 0.5, w, 1)
  c.strokeStyle = 'rgba(236,96,160,0.75)'
  c.lineWidth = 0.8
  for (let i = 1; i <= 6; i++) {
    const yy = hz + (y + h - hz) * Math.pow(i / 6, 1.8)
    c.beginPath()
    c.moveTo(x, yy)
    c.lineTo(x + w, yy)
    c.stroke()
  }
  for (let i = -8; i <= 8; i++) {
    c.beginPath()
    c.moveTo(cx + i * w * 0.03, hz)
    c.lineTo(cx + i * w * 0.16, y + h)
    c.stroke()
  }
  c.restore()
}

/* ---------- code ---------- */
const kw = (s) => new Set(s.split(' '))
const LANG = {
  rust: {
    kw: kw('use fn let mut for in return if else struct impl pub match'),
    com: '//',
    types: 1,
  },
  python: {
    kw: kw('from import class def for in return yield if else None True False'),
    com: '#',
    types: 1,
  },
  go: { kw: kw('package import func return var if for range nil'), com: '//', types: 1 },
  ts: { kw: kw('type export function const let return import from'), com: '//', types: 1 },
  c: { kw: kw('include typedef struct int char return if void'), com: '//', types: 1 },
  haskell: {
    kw: kw('module where data deriving let in if then else case of'),
    com: '--',
    types: 1,
  },
  sql: {
    kw: kw(
      'SELECT FROM JOIN ON WHERE GROUP BY HAVING ORDER LIMIT AS DESC COUNT AVG NOW INTERVAL AND',
    ),
    com: '--',
  },
  elixir: { kw: kw('defmodule def do end use defp __MODULE__'), com: '#', types: 1, atoms: 1 },
  swift: { kw: kw('import struct let var some private return'), com: '//', types: 1 },
  clojure: { kw: kw('ns defn let fn'), com: ';', atoms: 1, lisp: 1 },
  ruby: { kw: kw('class def end include new'), com: '#', types: 1, atoms: 1 },
  pascal: { kw: kw('program uses var begin end for to downto do integer'), com: '{', ci: 1 },
}
const THEME = {
  dark: {
    bg: '#211b17',
    bar: '#2d2520',
    gut: '#64564b',
    hl: 'rgba(239,200,130,0.07)',
    txt: '#eadfca',
    kw: '#e8874a',
    str: '#a8c46a',
    com: '#86766a',
    num: '#e0ae45',
    type: '#73b9b4',
    fn: '#efc77c',
    atom: '#d083a8',
  },
  light: {
    bg: '#f2e9d6',
    bar: '#e2d6bd',
    gut: '#a8977f',
    hl: 'rgba(217,98,43,0.08)',
    txt: '#3a2e25',
    kw: '#b4441f',
    str: '#4c7a28',
    com: '#9b8a74',
    num: '#9a6512',
    type: '#1d6c70',
    fn: '#7b4a10',
    atom: '#8e3766',
  },
}
function tokenize(ln, L) {
  const out = []
  let i = 0
  const re =
    /"(?:[^"\\]|\\.)*"|'(?:[^'\\]|\\.)*'|#?\$[0-9A-Fa-f]+|\d[\d_.]*|:[A-Za-z_][\w?!]*|[A-Za-z_@][\w!?]*|\s+|./y
  while (i < ln.length) {
    if (L.com && ln.startsWith(L.com, i)) {
      out.push([ln.slice(i), 'com'])
      break
    }
    re.lastIndex = i
    const t = re.exec(ln)[0]
    let k = 'txt'
    if (t[0] === '"' || t[0] === "'") k = 'str'
    else if (/^#?\$|^\d/.test(t)) k = 'num'
    else if (t[0] === ':' && t.length > 1) k = L.atoms ? 'atom' : 'txt'
    else if (t[0] === '@') k = 'atom'
    else if (/^[A-Za-z_]/.test(t)) {
      if (L.kw.has(L.ci ? t.toLowerCase() : t)) k = 'kw'
      else if (L.lisp && ln[i - 1] === '(') k = 'fn'
      else if (L.types && /^[A-Z]/.test(t)) k = 'type'
      else if (ln[i + t.length] === '(') k = 'fn'
    }
    out.push([t, k])
    i += t.length
  }
  return out
}
function codeLine(ln, L, x, y, fs, pal) {
  for (const [s, k] of tokenize(ln, L)) {
    c.font = `${k === 'com' ? 'italic ' : ''}${k === 'kw' ? 500 : 400} ${fs}px ${MONO}`
    c.fillStyle = pal[k]
    c.textAlign = 'left'
    c.fillText(s, x, y)
    x += c.measureText(s).width
  }
}
function editor(W, H, f) {
  const t = THEME[f.theme],
    L = LANG[f.lang],
    lines = f.code.split('\n'),
    lh = 20,
    y0 = 43
  rr(0, 0, W, H, 0, t.bg)
  c.fillStyle = t.bar
  c.fillRect(0, 0, W, 24)
  c.font = `500 10.5px ${SANS}`
  const tw = c.measureText(f.file).width
  rr(8, 5, tw + 30, 19, [5, 5, 0, 0], t.bg)
  circ(18, 14.5, 2.5, t.kw)
  tx(f.file, 26, 18.5, 10.5, t.txt, { w: 500 })
  tx(f.label, W - 12, 17, 8.5, t.gut, { mono: 1, al: 'right', ls: 1.2, w: 600 })
  if (f.hl) {
    c.fillStyle = t.hl
    c.fillRect(0, y0 + (f.hl - 1) * lh - 14, W, lh)
  }
  lines.forEach((ln, i) => {
    const y = y0 + i * lh
    tx(String(i + 1), 26, y, 10, t.gut, { mono: 1, al: 'right' })
    codeLine(ln, L, 38, y, 13, t)
  })
}
function turbo(W, H, f) {
  const pal = {
    txt: '#f3d25a',
    kw: '#ffffff',
    str: '#7fe3e3',
    num: '#7fe3e3',
    com: '#9fb0e8',
    type: '#f3d25a',
    fn: '#f3d25a',
    atom: '#f3d25a',
  }
  rr(0, 0, W, H, 0, '#1d2a8c')
  c.fillStyle = '#c9c3b3'
  c.fillRect(0, 0, W, 18)
  c.fillRect(0, H - 18, W, 18)
  let x = 10
  for (const m of ['File', 'Edit', 'Search', 'Run', 'Compile', 'Debug', 'Options']) {
    tx(m[0], x, 13, 10, '#b3261e', { mono: 1, w: 500 })
    c.font = `500 10px ${MONO}`
    const w0 = c.measureText(m[0]).width
    tx(m.slice(1), x + w0, 13, 10, '#1b1b1b', { mono: 1, w: 500 })
    x += c.measureText(m).width + 16
  }
  x = 10
  for (const [k, v] of [
    ['F1', 'Help'],
    ['F2', 'Save'],
    ['F3', 'Open'],
    ['Alt-F9', 'Compile'],
    ['F9', 'Make'],
  ]) {
    tx(k, x, H - 5, 9.5, '#b3261e', { mono: 1, w: 500 })
    c.font = `500 9.5px ${MONO}`
    const w0 = c.measureText(k + ' ').width
    tx(v, x + w0, H - 5, 9.5, '#1b1b1b', { mono: 1, w: 500 })
    x += c.measureText(k + ' ' + v).width + 14
  }
  c.strokeStyle = '#e8e2cc'
  c.lineWidth = 1
  c.strokeRect(6.5, 25.5, W - 13, H - 50)
  c.strokeRect(9.5, 28.5, W - 19, H - 56)
  c.font = `500 10px ${MONO}`
  const tl = ' REEL.PAS ',
    tw = c.measureText(tl).width
  c.fillStyle = '#1d2a8c'
  c.fillRect(W / 2 - tw / 2, 22, tw, 10)
  tx(tl, W / 2, 30, 10, '#ffffff', { mono: 1, w: 500, al: 'center' })
  c.fillStyle = '#1d2a8c'
  c.fillRect(24, H - 30, 52, 10)
  tx(' 9:14 ', 50, H - 22, 9, '#e8e2cc', { mono: 1, al: 'center' })
  f.code.split('\n').forEach((ln, i) => codeLine(ln, LANG.pascal, 22, 50 + i * 18.5, 12.5, pal))
  c.fillStyle = '#f3d25a'
  c.fillRect(22 + 7.5 * 13, 50 + 8 * 18.5 + 2, 7.5, 2)
}
function crt(W, H, f) {
  rr(0, 0, W, H, 0, '#2b2622')
  const sx = 16,
    sy = 12,
    sw = W - 32,
    sh = H - 24
  c.save()
  c.beginPath()
  c.roundRect(sx, sy, sw, sh, 24)
  c.clip()
  c.fillStyle = f.bg
  c.fillRect(sx, sy, sw, sh)
  c.shadowColor = f.fg
  c.shadowBlur = 7
  const lines = f.code.split('\n')
  lines.forEach((ln, i) => tx(ln, sx + 20, sy + 28 + i * 19.5, 13.5, f.fg, { mono: 1, w: 600 }))
  if (f.cursor) {
    c.font = `600 13.5px ${MONO}`
    const last = lines[lines.length - 1]
    const w = c.measureText(last).width
    c.fillStyle = f.fg
    c.fillRect(sx + 20 + w + 1, sy + 28 + (lines.length - 1) * 19.5 - 11, 8, 13)
  }
  c.shadowBlur = 0
  c.fillStyle = 'rgba(0,0,0,0.28)'
  for (let y = sy; y < sy + sh; y += 3) c.fillRect(sx, y, sw, 1)
  let g = c.createRadialGradient(W / 2, H / 2, sw * 0.25, W / 2, H / 2, sw * 0.72)
  g.addColorStop(0, 'rgba(0,0,0,0)')
  g.addColorStop(1, 'rgba(0,0,0,0.6)')
  c.fillStyle = g
  c.fillRect(sx, sy, sw, sh)
  g = c.createLinearGradient(sx, sy, sx + sw * 0.5, sy + sh * 0.6)
  g.addColorStop(0, 'rgba(255,255,255,0.09)')
  g.addColorStop(1, 'rgba(255,255,255,0)')
  c.fillStyle = g
  c.fillRect(sx, sy, sw, sh)
  c.restore()
  rr(sx, sy, sw, sh, 24, null, 'rgba(0,0,0,0.7)', 3)
}

const CODE = {
  rust: {
    file: 'main.rs',
    label: 'RUST',
    theme: 'dark',
    lang: 'rust',
    hl: 6,
    code: `use std::collections::HashMap;

fn count(text: &str) -> HashMap<&str, u32> {
    let mut map = HashMap::new();
    for w in text.split_whitespace() {
        *map.entry(w).or_insert(0) += 1;
    }
    map
}

fn main() {
    let m = count("to be or not to be");
    println!("{:?}", m.get("be"));
}`,
  },
  python: {
    file: 'reel.py',
    label: 'PYTHON',
    theme: 'light',
    lang: 'python',
    hl: 9,
    code: `from dataclasses import dataclass

@dataclass
class Frame:
    index: int
    tag: str = "code"

def rewind(frames, step=1):
    """Yield frames in reverse order."""
    for f in reversed(frames[::step]):
        yield f

reel = [Frame(i) for i in range(24)]
print(next(rewind(reel)).index)  # 23`,
  },
  go: {
    file: 'server.go',
    label: 'GO',
    theme: 'dark',
    lang: 'go',
    hl: 7,
    code: `package main

import "fmt"
import "net/http"

func hi(w http.ResponseWriter, r *http.Request) {
    fmt.Fprintf(w, "frame %s", r.URL.Path)
}

func main() {
    http.HandleFunc("/", hi)
    http.ListenAndServe(":8080", nil)
}`,
  },
  ts: {
    file: 'useReel.ts',
    label: 'TYPESCRIPT',
    theme: 'dark',
    lang: 'ts',
    hl: 7,
    code: `type Frame = { id: number; kind: "code" | "ui" };

export function useReel(frames: Frame[]) {
  const [pos, setPos] = useState(0);
  const n = frames.length;

  const rewind = useCallback(() => {
    setPos((p) => (p - 1 + n) % n);
  }, [n]);

  return { frame: frames[pos], rewind };
}`,
  },
  c: {
    file: 'ring.c',
    label: 'C',
    theme: 'light',
    lang: 'c',
    hl: 10,
    code: `#include <stdio.h>

typedef struct {
    int head, tail;
    char buf[64];
} Ring;

int ring_push(Ring *r, char c) {
    int next = (r->head + 1) % 64;
    if (next == r->tail) return -1;
    r->buf[r->head] = c;
    r->head = next;
    return 0;
}`,
  },
  haskell: {
    file: 'Reel.hs',
    label: 'HASKELL',
    theme: 'dark',
    lang: 'haskell',
    hl: 7,
    code: `module Reel where

data Frame = Code String | Shot Int
  deriving (Show, Eq)

rewind :: [a] -> [a]
rewind = foldl (flip (:)) []

loop :: [a] -> [a]
loop xs = xs ++ loop xs

main :: IO ()
main = print . take 3 . rewind $ [1..9]`,
  },
  sql: {
    file: 'frames.sql',
    label: 'SQL',
    theme: 'light',
    lang: 'sql',
    hl: 7,
    code: `-- frames shot per project, last 30 days
SELECT p.name,
       COUNT(f.id)      AS frames,
       AVG(f.duration)  AS avg_ms
FROM   projects p
JOIN   frames f ON f.project_id = p.id
WHERE  f.created_at > NOW() - INTERVAL '30 days'
GROUP  BY p.name
HAVING COUNT(f.id) > 24
ORDER  BY frames DESC
LIMIT  10;`,
  },
  elixir: {
    file: 'reel.ex',
    label: 'ELIXIR',
    theme: 'dark',
    lang: 'elixir',
    hl: 11,
    code: `defmodule Reel do
  use GenServer

  def start_link(frames) do
    GenServer.start_link(__MODULE__, frames)
  end

  def init(frames), do: {:ok, {frames, 0}}

  def handle_call(:next, _from, {fs, i}) do
    n = rem(i + 1, length(fs))
    {:reply, Enum.at(fs, n), {fs, n}}
  end
end`,
  },
  swift: {
    file: 'FrameView.swift',
    label: 'SWIFT',
    theme: 'light',
    lang: 'swift',
    hl: 9,
    code: `import SwiftUI

struct FrameView: View {
    let title: String
    @State private var lit = false

    var body: some View {
        Text(title)
            .font(.title.monospaced())
            .opacity(lit ? 1 : 0.4)
            .onAppear { lit = true }
    }
}`,
  },
  clojure: {
    file: 'core.clj',
    label: 'CLOJURE',
    theme: 'dark',
    lang: 'clojure',
    hl: 10,
    code: `(ns reel.core
  (:require [clojure.string :as str]))

(defn frames [n]
  (map #(hash-map :id % :kind :code) (range n)))

(defn rewind [reel]
  (reverse reel))

(->> (frames 24)
     rewind
     (take 3)
     (map :id))   ; => (23 22 21)`,
  },
  ruby: {
    file: 'reel.rb',
    label: 'RUBY',
    theme: 'light',
    lang: 'ruby',
    hl: 9,
    code: `class Reel
  include Enumerable

  def initialize(*frames)
    @frames = frames
  end

  def each(&block)
    @frames.reverse_each(&block)
  end
end

reel = Reel.new(:ui, :code, :arch)
puts reel.map(&:to_s).join(" <- ")`,
  },
  pascal: {
    code: `program Reel;
uses Crt;
var i: Integer;
begin
  ClrScr;
  for i := 24 downto 1 do
  begin
    GotoXY(10, 5);
    Write('FRAME ', i:2);
    Delay(40)
  end;
  WriteLn('REWOUND.')
end.`,
  },
  basic: {
    bg: '#0b160d',
    fg: '#86f59c',
    cursor: 1,
    code: `]LIST
10 REM *** REEL COUNTER ***
20 FOR F = 24 TO 1 STEP -1
30 PRINT "FRAME ";F
40 FOR D = 1 TO 200 : NEXT D
50 NEXT F
60 PRINT "REWIND COMPLETE"
70 END
]RUN
FRAME 24
FRAME 23
FRAME 22
]`,
  },
  asm: {
    bg: '#170e05',
    fg: '#ffb347',
    code: `; REWIND COUNTER -- 6502
        LDX #$18      ; 24 FRAMES
LOOP    TXA
        STA $0400     ; SCREEN RAM
        JSR DELAY
        DEX
        BNE LOOP
        RTS
DELAY   LDY #$FF
WAIT    DEY
        BNE WAIT
        RTS`,
  },
}

/* ---------- design ---------- */
function dMobile(W, H) {
  rr(0, 0, W, H, 0, '#e6d8bd')
  tx('PLAYER FLOW · V3', 16, 24, 8.5, P.brown, { mono: 1, w: 600, ls: 1.2 })
  const pw = 114,
    ph = 258,
    gap = 34,
    x0 = (W - (3 * pw + 2 * gap)) / 2,
    y = 44,
    sw = pw - 10,
    sh = ph - 10,
    sy = y + 5
  for (let i = 0; i < 3; i++) {
    const x = x0 + i * (pw + gap)
    rr(x + 3, y + 6, pw, ph, 18, 'rgba(70,40,20,0.2)')
    rr(x, y, pw, ph, 18, P.ink)
  }
  let x = x0 + 5
  rr(x, sy, sw, sh, 14, P.navy)
  sunset(x + 10, sy + 16, sw - 20, sw - 20, 6)
  const ay = sy + sw
  tx('Night Drive', x + 10, ay + 12, 11, P.cream, { w: 600 })
  tx('Reel Tapes · 1986', x + 10, ay + 25, 7.5, '#a9a3b8')
  pill(x + 10, ay + 36, sw - 20, 3, 'rgba(239,228,204,0.25)')
  pill(x + 10, ay + 36, (sw - 20) * 0.42, 3, P.orange)
  circ(x + 10 + (sw - 20) * 0.42, ay + 37.5, 4, P.cream)
  tx('1:42', x + 10, ay + 52, 6.5, '#a9a3b8', { mono: 1 })
  tx('4:05', x + sw - 10, ay + 52, 6.5, '#a9a3b8', { mono: 1, al: 'right' })
  const cx = x + sw / 2,
    cy = ay + 80
  circ(cx, cy, 15, P.orange)
  tri(cx - 4, cy - 6, cx - 4, cy + 6, cx + 7, cy, P.cream)
  tri(cx - 31, cy, cx - 25, cy - 5, cx - 25, cy + 5, P.cream)
  tri(cx - 25, cy, cx - 19, cy - 5, cx - 19, cy + 5, P.cream)
  tri(cx + 31, cy, cx + 25, cy - 5, cx + 25, cy + 5, P.cream)
  tri(cx + 25, cy, cx + 19, cy - 5, cx + 19, cy + 5, P.cream)
  x = x0 + pw + gap + 5
  rr(x, sy, sw, sh, 14, P.paper)
  tx('Library', x + 10, sy + 26, 13, P.ink, { w: 700 })
  rr(x + 10, sy + 36, sw - 20, 16, 8, '#e6d9c0')
  tx('Search', x + 20, sy + 47, 7, P.muted)
  const cl = [P.orange, P.teal, P.mustard, P.magenta, P.sage, P.navy]
  for (let i = 0; i < 6; i++) {
    const yy = sy + 64 + i * 29
    rr(x + 10, yy, 22, 22, 4, cl[i])
    pill(x + 38, yy + 4, sw - 66 - (i % 3) * 8, 5, '#5b4a3e')
    pill(x + 38, yy + 13, 34 + ((i * 9) % 22), 4, '#cdbfa5')
  }
  x = x0 + 2 * (pw + gap) + 5
  rr(x, sy, sw, sh, 14, '#f7efdf')
  tx('THIS WEEK', x + 10, sy + 24, 7, P.muted, { mono: 1, ls: 1 })
  tx('24h 18m', x + 10, sy + 46, 18, P.ink, { w: 700 })
  tx('+3h vs last week', x + 10, sy + 59, 7.5, P.teal, { w: 600 })
  const vals = [0.4, 0.65, 0.5, 0.9, 0.7, 0.35, 0.8],
    bw = 8,
    bg = (sw - 20 - 7 * bw) / 6,
    base = sy + 150
  vals.forEach((v, i) => {
    const bx = x + 10 + i * (bw + bg)
    rr(bx, base - 70 * v, bw, 70 * v, 3, i === 3 ? P.orange : '#e3c48a')
    tx('MTWTFSS'[i], bx + bw / 2, base + 11, 6.5, P.muted, { mono: 1, al: 'center' })
  })
  ;[
    [P.teal, 0.7],
    [P.magenta, 0.5],
  ].forEach(([col, w2], i) => {
    const yy = sy + 172 + i * 36
    rr(x + 10, yy, sw - 20, 30, 6, P.cream)
    circ(x + 22, yy + 15, 6, col)
    pill(x + 34, yy + 9, (sw - 54) * w2 + 10, 4.5, '#5b4a3e')
    pill(x + 34, yy + 18, (sw - 54) * 0.5, 4, '#cdbfa5')
  })
}
function dDash(W, H) {
  rr(0, 0, W, H, 0, P.paper)
  c.fillStyle = '#3a2a20'
  c.fillRect(0, 0, 58, H)
  circ(29, 24, 10, P.orange)
  circ(29, 24, 4, '#3a2a20')
  for (let i = 0; i < 5; i++)
    rr(19, 56 + i * 30, 20, 20, 5, i === 0 ? 'rgba(239,228,204,0.9)' : 'rgba(239,228,204,0.18)')
  tx('Overview', 74, 30, 16, P.ink, { w: 600 })
  tx('Q2 · 1986', 74, 44, 8.5, P.muted, { mono: 1 })
  rr(W - 90, 16, 76, 22, 11, null, P.line, 1)
  tx('Export', W - 52, 31, 8.5, P.ink, { al: 'center', w: 500 })
  const kx = 74,
    kw2 = (W - kx - 14 - 16) / 3,
    ky = 56,
    kh = 58
  ;[
    ['FRAMES', '24.8k', '+12.4%'],
    ['PROJECTS', '318', '+6'],
    ['UPTIME', '99.97%', '30d'],
  ].forEach(([l, v, d], i) => {
    const x = kx + i * (kw2 + 8)
    rr(x, ky, kw2, kh, 8, P.card, P.line, 1)
    tx(l, x + 10, ky + 16, 7.5, P.muted, { mono: 1, ls: 1 })
    tx(v, x + 10, ky + 42, 17, P.ink, { w: 700 })
    tx(d, x + kw2 - 10, ky + 42, 8, i === 2 ? P.muted : P.teal, { al: 'right', w: 600 })
  })
  const cx0 = 74,
    cy0 = 124,
    cw = 232,
    ch = 150
  rr(cx0, cy0, cw, ch, 8, P.card, P.line, 1)
  tx('Frames per day', cx0 + 10, cy0 + 18, 9, P.ink, { w: 600 })
  const gx0 = cx0 + 14,
    gx1 = cx0 + cw - 14,
    gy0 = cy0 + 34,
    gy1 = cy0 + ch - 20
  for (let i = 0; i < 4; i++)
    line(
      [
        [gx0, gy0 + (i * (gy1 - gy0)) / 3],
        [gx1, gy0 + (i * (gy1 - gy0)) / 3],
      ],
      '#ebe0c9',
      1,
    )
  const d = [0.3, 0.42, 0.38, 0.5, 0.47, 0.62, 0.55, 0.7, 0.66, 0.78, 0.72, 0.85, 0.8, 0.92]
  const pts = d.map((v, i) => [gx0 + (i * (gx1 - gx0)) / (d.length - 1), gy1 - v * (gy1 - gy0)])
  c.beginPath()
  c.moveTo(gx0, gy1)
  pts.forEach(([x, y]) => c.lineTo(x, y))
  c.lineTo(gx1, gy1)
  c.closePath()
  c.fillStyle = 'rgba(46,139,139,0.16)'
  c.fill()
  line(pts, P.teal, 2)
  circ(pts[pts.length - 1][0], pts[pts.length - 1][1], 3.5, P.paper, P.teal, 2)
  ;['MAY 1', 'MAY 7', 'MAY 14'].forEach((s, i) =>
    tx(s, gx0 + (i * (gx1 - gx0)) / 2, gy1 + 13, 6.5, P.muted, {
      mono: 1,
      al: ['left', 'center', 'right'][i],
    }),
  )
  const bx0 = cx0 + cw + 8,
    bw = W - 14 - bx0
  rr(bx0, cy0, bw, ch, 8, P.card, P.line, 1)
  tx('By language', bx0 + 10, cy0 + 18, 9, P.ink, { w: 600 })
  ;[
    ['Rust', 0.9],
    ['Go', 0.72],
    ['TS', 0.64],
    ['Python', 0.5],
    ['SQL', 0.3],
  ].forEach(([n, v], i) => {
    const y = cy0 + 36 + i * 21
    tx(n, bx0 + 10, y + 8, 7.5, P.brown, { mono: 1 })
    pill(bx0 + 50, y, (bw - 62) * v, 9, i % 2 ? P.mustard : P.orange)
  })
  rr(74, 284, W - 88, 28, 6, P.card, P.line, 1)
  circ(88, 298, 5, P.orange)
  pill(100, 295.5, 90, 5, '#5b4a3e')
  pill(220, 295.5, 60, 5, '#cdbfa5')
  rr(W - 70, 291, 44, 14, 7, '#d7e6dd')
  tx('LIVE', W - 48, 301, 6.5, P.teal, { mono: 1, al: 'center', w: 600 })
}
function dLanding(W, H) {
  rr(0, 0, W, H, 0, P.paper)
  tx('reel.', 18, 25, 15, P.ink, { w: 700 })
  ;['Work', 'Process', 'Studio'].forEach((s, i) => tx(s, 250 + i * 48, 23, 9, P.brown, { w: 500 }))
  pill(W - 86, 10, 70, 20, P.ink)
  tx('Contact', W - 51, 23.5, 8.5, P.cream, { al: 'center', w: 500 })
  line(
    [
      [0, 38.5],
      [W, 38.5],
    ],
    P.line,
    1,
  )
  tx('Every frame,', 18, 84, 27, P.ink, { w: 700 })
  tx('in one loop.', 18, 114, 27, P.orange, { w: 700 })
  pill(18, 130, 200, 5, '#cbbca0')
  pill(18, 141, 160, 5, '#cbbca0')
  pill(18, 158, 88, 24, P.orange)
  tx('Start a reel', 62, 173.5, 9, P.cream, { al: 'center', w: 600 })
  rr(114, 158, 74, 24, 12, null, P.ink, 1.2)
  tx('Showreel', 151, 173.5, 9, P.ink, { al: 'center', w: 500 })
  sunset(262, 52, 205, 136, 8)
  line(
    [
      [18, 206.5],
      [W - 18, 206.5],
    ],
    P.line,
    1,
  )
  const fc = [P.teal, P.mustard, P.magenta],
    ft = ['Code', 'Design', 'Systems']
  for (let i = 0; i < 3; i++) {
    const x = 18 + i * 152
    circ(x + 11, 228, 11, fc[i])
    tx(ft[i], x + 30, 232, 11, P.ink, { w: 600 })
    pill(x, 250, 130, 5, '#cbbca0')
    pill(x, 261, 118, 5, '#cbbca0')
    pill(x, 272, 90, 5, '#cbbca0')
  }
  c.fillStyle = P.ink
  c.fillRect(0, 294, W, H - 294)
  tx('© 1986 Reel Studio', 18, 312, 8, '#a8977c', { mono: 1 })
}
function dPalette(W, H) {
  rr(0, 0, W, H, 0, P.paper)
  tx('Aa', 16, 126, 104, P.ink, { w: 700 })
  tx('PLEX SANS · BOLD', 22, 150, 8, P.muted, { mono: 1, ls: 1.2 })
  line(
    [
      [18, 164.5],
      [218, 164.5],
    ],
    P.line,
    1,
  )
  tx('Headline 32', 18, 196, 22, P.ink, { w: 600 })
  tx('Title 20', 18, 226, 15, P.ink, { w: 500 })
  tx('Body 14 — set in 1.5 leading', 18, 250, 10.5, P.brown)
  tx('CAPTION 10', 18, 272, 8, P.muted, { mono: 1, ls: 1.2 })
  const sw = [
      ['#D9622B', 'Rust'],
      ['#E0A83A', 'Mustard'],
      ['#2E8B8B', 'Teal'],
      ['#C2457A', 'Rose'],
      ['#1F2A44', 'Navy'],
    ],
    x0 = 240,
    w = 42,
    g = 4
  sw.forEach(([hex, n], i) => {
    const x = x0 + i * (w + g)
    rr(x, 20, w, 186, 6, hex)
    tx(n, x + 4, 224, 8, P.ink, { w: 600 })
    tx(hex, x + 4, 236, 7, P.muted, { mono: 1 })
  })
  ;['#f6d9c8', '#efb393', '#e78a5f', '#d9622b', '#a8461b'].forEach((t, i) =>
    rr(x0 + i * (w + g), 252, w, 22, 4, t),
  )
  tx('TINTS · RUST 100–500', x0, 292, 7.5, P.muted, { mono: 1, ls: 1 })
}
function toggle(x, y, on) {
  pill(x, y, 36, 18, on ? P.teal : '#d8ccb4')
  circ(on ? x + 27 : x + 9, y + 9, 7, P.cream)
}
function dComponents(W, H) {
  rr(0, 0, W, H, 0, P.paper)
  const lab = (s, x, y) => tx(s, x, y, 7.5, P.muted, { mono: 1, ls: 1.2, w: 600 })
  lab('BUTTONS', 18, 22)
  pill(18, 30, 84, 26, P.orange)
  tx('Rewind', 60, 47, 9.5, P.cream, { al: 'center', w: 600 })
  rr(110, 30, 76, 26, 13, null, P.ink, 1.3)
  tx('Pause', 148, 47, 9.5, P.ink, { al: 'center', w: 600 })
  tx('Skip ›', 196, 47, 9.5, P.orange, { w: 600 })
  pill(250, 30, 84, 26, '#ddd1b9')
  tx('Disabled', 292, 47, 9.5, '#a19077', { al: 'center', w: 600 })
  lab('CONTROLS', 18, 84)
  toggle(18, 92, true)
  toggle(62, 92, false)
  rr(110, 93, 16, 16, 4, P.orange)
  line(
    [
      [114, 101],
      [117.5, 104.5],
      [122.5, 97.5],
    ],
    P.cream,
    2,
  )
  rr(134, 93, 16, 16, 4, null, P.muted, 1.3)
  circ(170, 101, 8, null, P.ink, 1.3)
  circ(170, 101, 3.5, P.ink)
  circ(194, 101, 8, null, P.muted, 1.3)
  lab('INPUT', 18, 138)
  rr(18, 146, 200, 32, 6, P.card, P.ink, 1.3)
  tx('Project name', 28, 158, 7, P.muted)
  tx('Möbius reel', 28, 171.5, 10, P.ink, { w: 500 })
  c.font = `500 10px ${SANS}`
  c.fillStyle = P.orange
  c.fillRect(29 + c.measureText('Möbius reel').width, 162, 1.3, 12)
  rr(18, 186, 200, 32, 6, P.card, P.magenta, 1.3)
  tx('Frame rate', 28, 198, 7, P.magenta)
  tx('24 fps', 28, 211.5, 10, P.ink)
  tx('Required field', 18, 231, 7.5, P.magenta)
  lab('TABS', 18, 258)
  tx('Code', 18, 280, 10, P.ink, { w: 600 })
  tx('Design', 62, 280, 10, P.muted, { w: 500 })
  tx('Systems', 114, 280, 10, P.muted, { w: 500 })
  line(
    [
      [18, 290.5],
      [218, 290.5],
    ],
    P.line,
    1,
  )
  c.fillStyle = P.orange
  c.fillRect(18, 289, 26, 2.5)
  lab('CHIPS', 250, 84)
  let cx = 250
  ;[
    ['Rust', 1],
    ['Go', 0],
    ['SQL', 0],
    ['UI', 1],
  ].forEach(([s, on]) => {
    c.font = `500 8.5px ${SANS}`
    const w = c.measureText(s).width + 20
    rr(cx, 92, w, 18, 9, on ? P.ink : null, on ? null : P.muted, 1.2)
    tx(s, cx + w / 2, 104, 8.5, on ? P.cream : P.ink, { al: 'center', w: 500 })
    cx += w + 6
  })
  lab('SLIDER', 250, 138)
  pill(250, 152, 200, 4, '#ddd1b9')
  pill(250, 152, 120, 4, P.teal)
  circ(370, 154, 8, P.cream, P.teal, 2)
  tx('0', 250, 176, 7.5, P.muted, { mono: 1 })
  tx('24', 450, 176, 7.5, P.muted, { mono: 1, al: 'right' })
  lab('CARD', 250, 200)
  rr(250, 208, 215, 92, 8, P.card, P.line, 1)
  sunset(260, 218, 60, 72, 5)
  tx('Night Drive', 330, 234, 10, P.ink, { w: 600 })
  pill(330, 242, 110, 4.5, '#cbbca0')
  pill(330, 252, 86, 4.5, '#cbbca0')
  rr(330, 268, 44, 16, 8, '#f6dcc9')
  tx('NEW', 352, 279, 7, P.orange, { mono: 1, w: 600, al: 'center' })
}
function dLogin(W, H) {
  rr(0, 0, W, H, 0, '#e6d8bd')
  tx('SIGN IN · SPEC', 16, 24, 8.5, P.brown, { mono: 1, w: 600, ls: 1.2 })
  const pw = 128,
    ph = 280,
    px = (W - pw) / 2,
    py = 24
  rr(px + 3, py + 6, pw, ph, 18, 'rgba(70,40,20,0.2)')
  rr(px, py, pw, ph, 18, P.ink)
  const x = px + 5,
    y = py + 5,
    w = pw - 10,
    m = x + w / 2,
    fx = x + 12,
    fw = w - 24,
    k = P.magenta
  rr(x, y, w, ph - 10, 14, P.paper)
  circ(m, y + 42, 15, P.orange)
  circ(m, y + 42, 6, P.paper)
  tx('Welcome back', m, y + 80, 11.5, P.ink, { w: 700, al: 'center' })
  tx('Sign in to your reel', m, y + 93, 7.5, P.muted, { al: 'center' })
  rr(fx, y + 108, fw, 26, 6, P.card, P.line, 1)
  tx('Email', fx + 8, y + 124.5, 7.5, P.muted)
  rr(fx, y + 142, fw, 26, 6, P.card, P.line, 1)
  tx('Password', fx + 8, y + 158.5, 7.5, P.muted)
  pill(fx, y + 182, fw, 28, P.orange)
  tx('Sign in', m, y + 199.5, 9, P.cream, { al: 'center', w: 600 })
  tx('Forgot password?', m, y + 228, 7.5, P.teal, { al: 'center', w: 500 })
  const dim = (x1, y1, x2, y2, l, lx, ly) => {
    line(
      [
        [x1, y1],
        [x2, y2],
      ],
      k,
      1,
    )
    if (x1 === x2) {
      line(
        [
          [x1 - 3, y1],
          [x1 + 3, y1],
        ],
        k,
        1,
      )
      line(
        [
          [x2 - 3, y2],
          [x2 + 3, y2],
        ],
        k,
        1,
      )
    } else {
      line(
        [
          [x1, y1 - 3],
          [x1, y1 + 3],
        ],
        k,
        1,
      )
      line(
        [
          [x2, y2 - 3],
          [x2, y2 + 3],
        ],
        k,
        1,
      )
    }
    tx(l, lx, ly, 7.5, k, { mono: 1, w: 600, al: 'center' })
  }
  dim(x, y + 104, fx, y + 104, '12', x + 6, y + 100)
  dim(fx + fw - 12, y + 134, fx + fw - 12, y + 142, '8', fx + fw - 3, y + 141)
  dim(px - 12, y + 182, px - 12, y + 210, '44', px - 26, y + 199)
  line(
    [
      [fx + 2, y + 121],
      [px - 40, y + 121],
      [px - 52, y + 110],
    ],
    k,
    1,
    [2, 2],
  )
  tx('Input / default', px - 56, y + 106, 8, k, { mono: 1, al: 'right' })
  line(
    [
      [fx + fw - 2, y + 196],
      [px + pw + 30, y + 196],
    ],
    k,
    1,
    [2, 2],
  )
  tx('Button / primary', px + pw + 34, y + 199, 8, k, { mono: 1 })
  line(
    [
      [m + 42, y + 77],
      [px + pw + 30, y + 77],
    ],
    k,
    1,
    [2, 2],
  )
  tx('Title · 11.5 / 700', px + pw + 34, y + 80, 8, k, { mono: 1 })
}
function dKanban(W, H) {
  rr(0, 0, W, H, 0, P.paper)
  tx('Sprint 14', 16, 27, 14, P.ink, { w: 600 })
  tx('MAY 12 – MAY 26', 92, 26, 7.5, P.muted, { mono: 1, ls: 1 })
  ;[P.magenta, P.mustard, P.teal].forEach((col, i) => circ(W - 52 + i * 14, 21, 8, col, P.paper, 2))
  const cols = [
    [
      'To do',
      P.muted,
      [
        ['UI', P.magenta, 2],
        ['API', P.teal, 1],
        ['Docs', P.muted, 2],
      ],
    ],
    [
      'In progress',
      P.mustard,
      [
        ['Arch', P.navy, 2],
        ['UI', P.magenta, 1],
      ],
    ],
    [
      'Done',
      P.teal,
      [
        ['Code', P.orange, 1],
        ['Code', P.orange, 2],
        ['Ops', P.sage, 1],
      ],
    ],
  ]
  const cw = (W - 32 - 16) / 3
  cols.forEach(([name, dot, cards], i) => {
    const x = 16 + i * (cw + 8)
    rr(x, 40, cw, H - 52, 8, '#ece2cd')
    circ(x + 12, 56, 3.5, dot)
    tx(name, x + 20, 59.5, 9, P.ink, { w: 600 })
    tx(String(cards.length), x + cw - 10, 59.5, 8, P.muted, { al: 'right', mono: 1 })
    let y = 70
    cards.forEach(([tag, tc, nb], j) => {
      const ch = 40 + nb * 9
      rr(x + 6, y, cw - 12, ch, 6, P.card, P.line, 1)
      c.font = `600 7px ${MONO}`
      const tw = c.measureText(tag).width + 12
      rr(x + 14, y + 8, tw, 12, 6, tc)
      tx(tag, x + 20, y + 17, 7, P.cream, { w: 600, mono: 1 })
      for (let b = 0; b < nb; b++)
        pill(
          x + 14,
          y + 28 + b * 9,
          (cw - 40) * (b ? 0.6 : 0.9),
          4.5,
          i === 2 ? '#cdbfa5' : '#8a7a66',
        )
      circ(x + cw - 20, y + ch - 11, 5, [P.teal, P.mustard, P.magenta][(i + j) % 3])
      y += ch + 7
    })
  })
}
function dGrid(W, H) {
  rr(0, 0, W, H, 0, '#f7f0e1')
  const M = 24,
    G = 8,
    cw = (W - 2 * M - 11 * G) / 12,
    X = (i) => M + i * (cw + G),
    SP = (n) => n * cw + (n - 1) * G,
    b = '#ddcfb3',
    b2 = '#cbbb9c'
  rr(X(0), 22, SP(12), 16, 3, b)
  rr(X(0), 50, SP(7), 120, 4, b2)
  pill(X(7), 54, SP(5), 8, '#8a7a66')
  pill(X(7), 68, SP(4), 8, '#8a7a66')
  for (let i = 0; i < 5; i++) pill(X(7), 88 + i * 11, SP(5) - (i % 2) * 20, 4.5, b2)
  rr(X(7), 148, SP(2), 22, 11, P.orange)
  for (let i = 0; i < 3; i++) {
    rr(X(i * 4), 184, SP(4), 104, 4, b)
    rr(X(i * 4) + 8, 192, SP(4) - 16, 50, 3, b2)
    pill(X(i * 4) + 8, 252, SP(3), 6, '#8a7a66')
    pill(X(i * 4) + 8, 266, SP(4) - 30, 4.5, b2)
    pill(X(i * 4) + 8, 276, SP(2), 4.5, b2)
  }
  for (let i = 0; i < 12; i++) {
    c.fillStyle = 'rgba(194,69,122,0.13)'
    c.fillRect(X(i), 0, cw, H)
    tx(String(i + 1), X(i) + cw / 2, 13, 6.5, P.magenta, { mono: 1, al: 'center', w: 600 })
  }
  c.fillStyle = 'rgba(194,69,122,0.55)'
  c.fillRect(M - 0.5, 0, 1, H)
  c.fillRect(W - M - 0.5, 0, 1, H)
  tx('12 COL · 8 GUTTER · 24 MARGIN', M + 4, H - 11, 8, P.magenta, { mono: 1, w: 600, ls: 1 })
}
function lem(cx, cy, a, col, lw) {
  c.beginPath()
  for (let i = 0; i <= 96; i++) {
    const t = (i / 96) * Math.PI * 2,
      d = 1 + Math.sin(t) ** 2
    const px = cx + (a * Math.cos(t)) / d,
      py = cy + (a * Math.sin(t) * Math.cos(t)) / d
    if (i) c.lineTo(px, py)
    else c.moveTo(px, py)
  }
  c.closePath()
  c.strokeStyle = col
  c.lineWidth = lw
  c.lineJoin = 'round'
  c.stroke()
}
function icon(i, x, y, col) {
  c.strokeStyle = col
  c.fillStyle = col
  c.lineWidth = 2
  c.lineJoin = 'round'
  const sq = (a, b, w, h) => {
    c.strokeRect(a, b, w, h)
  }
  switch (i) {
    case 0:
      tri(x - 5, y - 7, x - 5, y + 7, x + 7, y, col)
      break
    case 1:
      c.fillRect(x - 6, y - 7, 4, 14)
      c.fillRect(x + 2, y - 7, 4, 14)
      break
    case 2:
      tri(x - 9, y, x - 1, y - 6, x - 1, y + 6, col)
      tri(x - 1, y, x + 7, y - 6, x + 7, y + 6, col)
      break
    case 3:
      tri(x + 9, y, x + 1, y - 6, x + 1, y + 6, col)
      tri(x + 1, y, x - 7, y - 6, x - 7, y + 6, col)
      break
    case 4:
      c.fillRect(x - 6, y - 6, 12, 12)
      break
    case 5:
      circ(x, y, 7, P.orange)
      break
    case 6:
      sq(x - 9, y - 7, 18, 14)
      for (let k = 0; k < 3; k++) {
        c.fillRect(x - 6 + k * 5, y - 5, 2, 2)
        c.fillRect(x - 6 + k * 5, y + 3, 2, 2)
      }
      break
    case 7:
      lem(x, y, 10, col, 2)
      break
    case 8:
      tri(x, y - 8, x - 7, y + 1, x + 7, y + 1, col)
      c.fillRect(x - 7, y + 4, 14, 3)
      break
    case 9:
      sq(x - 7, y - 7, 6, 6)
      sq(x + 1, y - 7, 6, 6)
      sq(x - 7, y + 1, 6, 6)
      sq(x + 1, y + 1, 6, 6)
      break
    case 10:
      c.beginPath()
      c.moveTo(x - 9, y - 6)
      c.lineTo(x - 3, y - 6)
      c.lineTo(x - 1, y - 3)
      c.lineTo(x + 9, y - 3)
      c.lineTo(x + 9, y + 7)
      c.lineTo(x - 9, y + 7)
      c.closePath()
      c.stroke()
      break
    case 11:
      c.beginPath()
      c.moveTo(x - 5, y - 8)
      c.lineTo(x - 5, y + 7)
      c.lineTo(x - 1, y + 3)
      c.lineTo(x + 2, y + 9)
      c.lineTo(x + 4, y + 8)
      c.lineTo(x + 1, y + 2)
      c.lineTo(x + 6, y + 2)
      c.closePath()
      c.fill()
      break
  }
}
function dIcons(W, H) {
  rr(0, 0, W, H, 0, P.navy)
  const lc = '#8f97b0'
  tx('ICONOGRAPHY · 24 GRID', 18, 24, 8, lc, { mono: 1, w: 600, ls: 1.2 })
  ;[
    [P.orange, P.cream],
    [P.cream, P.ink],
    [P.teal, P.cream],
  ].forEach(([bg, fg], i) => {
    const x = 18 + i * 90
    rr(x, 42, 76, 76, 18, bg)
    lem(x + 38, 80, 26, fg, 6)
  })
  ;['Primary', 'Mono', 'Alt'].forEach((s, i) =>
    tx(s, 18 + i * 90 + 38, 134, 7.5, lc, { al: 'center', mono: 1 }),
  )
  for (let i = 0; i < 12; i++) {
    const x = 296 + (i % 4) * 44,
      y = 42 + Math.floor(i / 4) * 44
    rr(x, y, 40, 40, 4, 'rgba(239,228,204,0.05)', 'rgba(239,228,204,0.14)', 1)
    icon(i, x + 20, y + 20, P.cream)
  }
  line(
    [
      [18, 190.5],
      [W - 18, 190.5],
    ],
    'rgba(239,228,204,0.15)',
    1,
  )
  tx('reel.', 16, 256, 48, P.cream, { w: 700 })
  tx('STROKE 2 · RADIUS 2 · 24×24', 18, 286, 7.5, lc, { mono: 1, ls: 1 })
  ;[P.orange, P.mustard, P.teal, P.magenta, P.cream].forEach((col, i) =>
    circ(330 + i * 28, 244, 10, col),
  )
}

/* ---------- architecture ---------- */
const BP = {
  bg: '#1e3d52',
  grid: 'rgba(220,235,240,0.07)',
  grid2: 'rgba(220,235,240,0.13)',
  ink: '#e9e1cc',
  fill: 'rgba(233,225,204,0.07)',
  acc: '#eaa944',
  mut: 'rgba(233,225,204,0.6)',
}
const PA2 = {
  bg: '#f1e8d3',
  grid: 'rgba(70,45,25,0.07)',
  grid2: 'rgba(70,45,25,0.12)',
  ink: '#2e241d',
  fill: '#f8f1e2',
  acc: '#cf5527',
  mut: '#8c7b66',
}
function sheet(W, H, s, title) {
  rr(0, 0, W, H, 0, s.bg)
  for (let x = 0; x < W; x += 12) {
    c.fillStyle = x % 48 ? s.grid : s.grid2
    c.fillRect(x, 0, 1, H)
  }
  for (let y = 0; y < H; y += 12) {
    c.fillStyle = y % 48 ? s.grid : s.grid2
    c.fillRect(0, y, W, 1)
  }
  if (title) tx(title, 14, 20, 8.5, s.mut, { mono: 1, w: 600, ls: 1.4 })
}
function box(x, y, w, h, label, s, o = {}) {
  rr(x, y, w, h, o.r ?? 4, o.fill || s.fill, o.acc ? s.acc : s.ink, o.lw || 1.3)
  tx(label, x + w / 2, y + h / 2 + (o.sub ? -1 : 3.5), o.fs || 9.5, s.ink, {
    al: 'center',
    w: 600,
    mono: o.mono,
  })
  if (o.sub) tx(o.sub, x + w / 2, y + h / 2 + 10, 7, s.mut, { al: 'center', mono: 1 })
}
function cyl(cx, y, w, h, label, s) {
  const rx = w / 2,
    ry = Math.min(7, h * 0.16)
  c.beginPath()
  c.moveTo(cx - rx, y + ry)
  c.lineTo(cx - rx, y + h - ry)
  c.ellipse(cx, y + h - ry, rx, ry, 0, Math.PI, 0, true)
  c.lineTo(cx + rx, y + ry)
  c.ellipse(cx, y + ry, rx, ry, 0, 0, Math.PI, true)
  c.closePath()
  c.fillStyle = s.bg
  c.fill()
  c.fillStyle = s.fill
  c.fill()
  c.strokeStyle = s.ink
  c.lineWidth = 1.3
  c.stroke()
  c.beginPath()
  c.ellipse(cx, y + ry, rx, ry, 0, 0, Math.PI * 2)
  c.stroke()
  if (label) tx(label, cx, y + h / 2 + ry / 2 + 3, 8.5, s.ink, { al: 'center', mono: 1, w: 600 })
}
function aMicro(W, H) {
  const s = BP
  sheet(W, H, s, 'SYSTEM OVERVIEW')
  box(14, 138, 62, 40, 'Client', s, { sub: 'web · ios' })
  arrow(
    [
      [76, 158],
      [104, 158],
    ],
    s.ink,
  )
  box(104, 128, 82, 60, 'Gateway', s, { acc: 1, sub: 'rate · auth' })
  ;[
    ['Auth', 46, 'users'],
    ['Orders', 122, 'orders'],
    ['Payments', 198, 'ledger'],
  ].forEach(([n, y, db]) => {
    box(226, y, 90, 36, n, s)
    arrow(
      [
        [186, 158],
        [206, 158],
        [206, y + 18],
        [226, y + 18],
      ],
      s.ink,
    )
    arrow(
      [
        [316, y + 18],
        [361, y + 18],
      ],
      s.ink,
    )
    cyl(390, y - 2, 56, 40, db, s)
  })
  rr(226, 258, 220, 22, 4, null, s.acc, 1.3, [4, 3])
  tx('event bus · kafka', 336, 272.5, 8.5, s.acc, { al: 'center', mono: 1, w: 600 })
  arrow(
    [
      [252, 234],
      [252, 258],
    ],
    s.acc,
    { dash: [3, 3] },
  )
  arrow(
    [
      [290, 234],
      [290, 258],
    ],
    s.acc,
    { dash: [3, 3] },
  )
  rr(14, H - 46, 150, 32, 2, null, s.mut, 1)
  line(
    [
      [14, H - 30],
      [164, H - 30],
    ],
    s.mut,
    1,
  )
  line(
    [
      [96, H - 46],
      [96, H - 14],
    ],
    s.mut,
    1,
  )
  tx('DWG 04', 20, H - 34, 7.5, s.ink, { mono: 1, w: 600 })
  tx('REV B', 102, H - 34, 7.5, s.acc, { mono: 1, w: 600 })
  tx('SHEET 1/3', 20, H - 18, 7.5, s.mut, { mono: 1 })
  tx('1986-04-12', 102, H - 18, 7.5, s.mut, { mono: 1 })
}
function aLayers(W, H) {
  const s = PA2
  sheet(W, H, s, '')
  const L = [
    ['PRESENTATION', ['Web app', 'Mobile', 'CLI']],
    ['APPLICATION', ['Use cases', 'Commands', 'Queries']],
    ['DOMAIN', ['Frame', 'Reel', 'Project']],
    ['INFRASTRUCTURE', ['Postgres', 'Object store', 'Queue']],
  ]
  const y0 = 14,
    bh = 64,
    g = 10,
    bx = 134,
    bw = (W - 50 - 10 - bx - 16) / 3
  L.forEach(([n, items], i) => {
    const y = y0 + i * (bh + g),
      dom = i === 2
    rr(14, y, W - 50, bh, 6, dom ? 'rgba(207,85,39,0.08)' : s.fill, dom ? s.acc : s.ink, 1.3)
    tx(n, 26, y + bh / 2 + 3, 8, dom ? s.acc : s.ink, { mono: 1, w: 600, ls: 1 })
    items.forEach((it, j) =>
      box(bx + j * (bw + 8), y + 15, bw, bh - 30, it, s, { fs: 9, fill: s.bg }),
    )
  })
  arrow(
    [
      [W - 20, y0 + 16],
      [W - 20, y0 + 4 * bh + 3 * g - 16],
    ],
    s.mut,
  )
  for (let i = 0; i < 4; i++) circ(W - 20, y0 + i * (bh + g) + bh / 2, 3, s.bg, s.mut, 1.2)
}
function aEvents(W, H) {
  const s = BP
  sheet(W, H, s, 'EVENT FLOW')
  tx('topic · orders.events', 240, 62, 8.5, s.acc, { al: 'center', mono: 1, w: 600 })
  const fill = [9, 7, 10]
  ;['Checkout', 'Inventory', 'Shipping'].forEach((n, i) => {
    const y = 74 + i * 64
    box(14, y, 80, 34, n, s, { fs: 9 })
    arrow(
      [
        [94, y + 17],
        [150, y + 17],
      ],
      s.ink,
    )
    tx('p' + i, 152, y + 1, 7, s.mut, { mono: 1 })
    for (let j = 0; j < 11; j++)
      rr(152 + j * 16, y + 5, 16, 24, 0, j < fill[i] ? 'rgba(234,169,68,0.28)' : null, s.ink, 1)
    tri(
      152 + (fill[i] - 3) * 16 + 8,
      y + 33,
      152 + (fill[i] - 3) * 16 + 4,
      y + 39,
      152 + (fill[i] - 3) * 16 + 12,
      y + 39,
      s.acc,
    )
    arrow(
      [
        [328, y + 17],
        [384, y + 17],
      ],
      s.ink,
    )
  })
  ;['Billing', 'Analytics', 'Notify'].forEach((n, i) =>
    box(384, 74 + i * 64, 86, 34, n, s, { fs: 9, acc: i === 1 }),
  )
  tx('consumer offset', 152, 290, 7.5, s.acc, { mono: 1 })
  tx('retention 7d', 328, 290, 7.5, s.mut, { mono: 1, al: 'right' })
}
function aSeq(W, H) {
  const s = PA2
  sheet(W, H, s, '')
  const xs = [62, 184, 306, 428],
    names = ['Client', 'API', 'Auth', 'DB']
  xs.forEach((x, i) => {
    box(x - 40, 14, 80, 24, names[i], s, { fs: 9 })
    line(
      [
        [x, 38],
        [x, H - 26],
      ],
      s.mut,
      1,
      [3, 3],
    )
  })
  rr(180, 60, 8, 166, 1, s.fill, s.ink, 1)
  rr(302, 90, 8, 104, 1, s.fill, s.ink, 1)
  rr(424, 120, 8, 40, 1, s.fill, s.ink, 1)
  ;[
    [0, 1, 'POST /login', 66, 0],
    [1, 2, 'verify(creds)', 96, 0],
    [2, 3, 'SELECT user', 126, 0],
    [3, 2, 'row', 156, 1],
    [2, 1, 'token', 188, 1],
    [1, 0, '200 OK', 220, 1],
  ].forEach(([a, b, l, y, ret]) => {
    const x1 = xs[a] + (a < b ? 4 : -4),
      x2 = xs[b] + (a < b ? -4 : 4)
    arrow(
      [
        [x1, y],
        [x2, y],
      ],
      ret ? s.mut : s.ink,
      { dash: ret ? [4, 3] : null },
    )
    tx(l, (x1 + x2) / 2, y - 5, 8, s.ink, { al: 'center', mono: 1 })
  })
  c.save()
  c.translate(306, 262)
  c.rotate(-0.03)
  rr(-58, -14, 116, 30, 2, '#f3d58f')
  tx('JWT · 15 min TTL', 0, 5, 8, s.ink, { al: 'center', mono: 1, w: 600 })
  c.restore()
  tx('SEQUENCE · LOGIN', 14, H - 10, 8, s.mut, { mono: 1, w: 600, ls: 1.4 })
}
function aCICD(W, H) {
  const s = BP
  sheet(W, H, s, 'PIPELINE · MAIN')
  const st = ['Commit', 'Build', 'Test', 'Stage', 'Prod'],
    t = ['0:04', '1:48', '3:12', 'running', '—'],
    step = (W - 28) / 5,
    y = 40,
    h = 36
  st.forEach((n, i) => {
    const x = 14 + i * step,
      w = step - 3
    c.beginPath()
    c.moveTo(x, y)
    c.lineTo(x + w - 10, y)
    c.lineTo(x + w, y + h / 2)
    c.lineTo(x + w - 10, y + h)
    c.lineTo(x, y + h)
    if (i) c.lineTo(x + 10, y + h / 2)
    c.closePath()
    c.fillStyle = i < 3 ? 'rgba(234,169,68,0.22)' : 'rgba(0,0,0,0)'
    c.fill()
    c.strokeStyle = i < 4 ? s.acc : s.mut
    c.lineWidth = 1.3
    c.setLineDash(i === 3 ? [4, 3] : [])
    c.stroke()
    c.setLineDash([])
    tx(n, x + w / 2 + (i ? 4 : 0), y + h / 2 + 3.5, 9.5, i < 4 ? s.ink : s.mut, {
      w: 600,
      al: 'center',
    })
    tx(t[i], x + w / 2, y + h + 14, 7.5, s.mut, { mono: 1, al: 'center' })
  })
  const gy = 196
  line(
    [
      [20, gy],
      [W - 20, gy],
    ],
    s.ink,
    1.6,
  )
  tx('main', 20, gy - 8, 8, s.ink, { mono: 1, w: 600 })
  c.beginPath()
  c.moveTo(120, gy)
  c.bezierCurveTo(140, gy, 140, gy - 44, 160, gy - 44)
  c.lineTo(290, gy - 44)
  c.bezierCurveTo(310, gy - 44, 310, gy, 330, gy)
  c.strokeStyle = s.acc
  c.lineWidth = 1.6
  c.stroke()
  c.beginPath()
  c.moveTo(352, gy)
  c.bezierCurveTo(368, gy, 368, gy + 40, 384, gy + 40)
  c.lineTo(404, gy + 40)
  c.bezierCurveTo(420, gy + 40, 420, gy, 436, gy)
  c.strokeStyle = '#7fc8c0'
  c.stroke()
  tx('feature/reel', 166, gy - 54, 8, s.acc, { mono: 1, w: 600 })
  tx('fix/perf', 360, gy + 58, 8, '#7fc8c0', { mono: 1, w: 600 })
  ;[40, 120, 330, 436].forEach((x) => circ(x, gy, 4.5, s.bg, s.ink, 1.6))
  ;[180, 230, 280].forEach((x) => circ(x, gy - 44, 4, s.bg, s.acc, 1.6))
  circ(394, gy + 40, 4, s.bg, '#7fc8c0', 1.6)
  rr(422, gy - 26, 28, 13, 6.5, s.acc)
  tx('v1.4', 436, gy - 16.5, 7, s.bg, { al: 'center', mono: 1, w: 600 })
}
function aK8s(W, H) {
  const s = PA2
  sheet(W, H, s, '')
  box(W / 2 - 56, 12, 112, 28, 'Ingress', s, { acc: 1, fs: 9.5 })
  rr(14, 62, W - 28, H - 74, 8, null, s.ink, 1.2, [5, 4])
  tx('cluster · prod-eu', 24, 78, 8, s.mut, { mono: 1, w: 600 })
  const nw = (W - 28 - 20 - 16) / 3,
    pods = [
      ['api', 'api', 'worker'],
      ['web', 'api'],
      ['worker', 'cron', 'web'],
    ],
    pc = { api: P.teal, worker: s.acc, web: P.magenta, cron: P.mustard },
    load = [0.62, 0.38, 0.81]
  for (let i = 0; i < 3; i++) {
    const x = 24 + i * (nw + 8),
      cx = x + nw / 2
    arrow(
      [
        [W / 2, 40],
        [W / 2, 50],
        [cx, 50],
        [cx, 88],
      ],
      s.ink,
    )
    rr(x, 88, nw, 210, 6, s.fill, s.ink, 1.2)
    tx(`node-${i + 1}`, x + 10, 104, 8.5, s.ink, { mono: 1, w: 600 })
    pods[i].forEach((p, j) => {
      const y = 114 + j * 38
      rr(x + 10, y, nw - 20, 30, 4, '#fffaf0', s.ink, 1)
      circ(x + 22, y + 15, 4, pc[p])
      tx(p, x + 32, y + 18.5, 8.5, s.ink, { mono: 1 })
      tx('2/2', x + nw - 18, y + 18.5, 7.5, s.mut, { mono: 1, al: 'right' })
    })
    tx('cpu', x + 10, 286, 7, s.mut, { mono: 1 })
    pill(x + 32, 281, nw - 44, 5, '#e3d6bd')
    pill(x + 32, 281, (nw - 44) * load[i], 5, s.acc)
  }
}
function aPipe(W, H) {
  const s = BP
  sheet(W, H, s, 'DATA PIPELINE · HOURLY')
  ;['App', 'CRM', 'Logs'].forEach((n, i) => {
    const y = 96 + i * 46
    box(12, y, 60, 30, n, s, { fs: 8.5 })
    arrow(
      [
        [72, y + 15],
        [86, y + 15],
        [86, 157],
        [98, 157],
      ],
      s.ink,
    )
  })
  box(98, 134, 62, 46, 'Ingest', s, { fs: 9, sub: 'stream' })
  arrow(
    [
      [160, 157],
      [178, 157],
    ],
    s.ink,
  )
  cyl(205, 130, 52, 56, 'lake', s)
  arrow(
    [
      [231, 157],
      [250, 157],
    ],
    s.ink,
  )
  box(250, 134, 66, 46, 'Transform', s, { fs: 8.5, sub: 'sql' })
  arrow(
    [
      [316, 157],
      [334, 157],
    ],
    s.ink,
  )
  cyl(361, 130, 52, 56, 'dwh', s)
  arrow(
    [
      [387, 157],
      [408, 157],
    ],
    s.ink,
  )
  rr(408, 126, 64, 62, 4, s.fill, s.acc, 1.3)
  ;[0.4, 0.7, 0.55, 0.9].forEach((v, i) => rr(418 + i * 11, 172 - 34 * v, 7, 34 * v, 1, s.acc))
  tx('BI', 440, 184, 7.5, s.ink, { mono: 1, w: 600, al: 'center' })
  const ty = 262
  line(
    [
      [20, ty],
      [W - 20, ty],
    ],
    s.mut,
    1,
  )
  for (let i = 0; i <= 24; i++) {
    const x = 20 + (i * (W - 40)) / 24
    line(
      [
        [x, ty - (i % 6 ? 3 : 6)],
        [x, ty],
      ],
      s.mut,
      1,
    )
    if (i < 24)
      rr(x + 3, ty - 14, (W - 40) / 24 - 6, 6, 1, i % 4 === 1 ? '#d9623b' : 'rgba(234,169,68,0.6)')
  }
  ;['00:00', '06:00', '12:00', '18:00', '24:00'].forEach((l, i) =>
    tx(l, 20 + (i * (W - 40)) / 4, ty + 14, 7, s.mut, {
      mono: 1,
      al: i === 0 ? 'left' : i === 4 ? 'right' : 'center',
    }),
  )
}
function table(x, y, w, name, rows, s) {
  const rh = 15,
    h = 20 + rows.length * rh + 4
  rr(x, y, w, h, 4, s.fill, s.ink, 1.2)
  rr(x, y, w, 20, [4, 4, 0, 0], s.ink)
  tx(name, x + 8, y + 14, 9, s.bg, { mono: 1, w: 600 })
  rows.forEach(([f, t, k], i) => {
    const yy = y + 20 + i * rh + 12
    if (k) tx(k, x + 8, yy, 6.5, s.acc, { mono: 1, w: 600 })
    tx(f, x + 26, yy, 8, s.ink, { mono: 1, w: k === 'PK' ? 600 : 400 })
    tx(t, x + w - 8, yy, 7.5, s.mut, { mono: 1, al: 'right' })
  })
}
function crow(x, y, dir, col) {
  line(
    [
      [x - 9 * dir, y],
      [x, y - 5],
    ],
    col,
    1.2,
  )
  line(
    [
      [x - 9 * dir, y],
      [x, y + 5],
    ],
    col,
    1.2,
  )
}
const ry = (y, i) => y + 20 + i * 15 + 7.5
function aER(W, H) {
  const s = PA2
  sheet(W, H, s, '')
  table(
    16,
    30,
    130,
    'users',
    [
      ['id', 'uuid', 'PK'],
      ['name', 'text'],
      ['email', 'text'],
      ['created', 'ts'],
    ],
    s,
  )
  table(
    178,
    30,
    130,
    'projects',
    [
      ['id', 'uuid', 'PK'],
      ['owner_id', 'uuid', 'FK'],
      ['title', 'text'],
      ['created', 'ts'],
    ],
    s,
  )
  table(
    340,
    30,
    130,
    'frames',
    [
      ['id', 'uuid', 'PK'],
      ['project_id', 'uuid', 'FK'],
      ['kind', 'enum'],
      ['idx', 'int'],
      ['payload', 'blob'],
    ],
    s,
  )
  table(
    178,
    190,
    130,
    'tags',
    [
      ['id', 'uuid', 'PK'],
      ['frame_id', 'uuid', 'FK'],
      ['label', 'text'],
    ],
    s,
  )
  line(
    [
      [146, ry(30, 0)],
      [162, ry(30, 0)],
      [162, ry(30, 1)],
      [178, ry(30, 1)],
    ],
    s.ink,
    1.2,
  )
  line(
    [
      [151, ry(30, 0) - 5],
      [151, ry(30, 0) + 5],
    ],
    s.ink,
    1.2,
  )
  crow(178, ry(30, 1), 1, s.ink)
  line(
    [
      [308, ry(30, 0)],
      [324, ry(30, 0)],
      [324, ry(30, 1)],
      [340, ry(30, 1)],
    ],
    s.ink,
    1.2,
  )
  line(
    [
      [313, ry(30, 0) - 5],
      [313, ry(30, 0) + 5],
    ],
    s.ink,
    1.2,
  )
  crow(340, ry(30, 1), 1, s.ink)
  line(
    [
      [405, 133],
      [405, ry(190, 1)],
      [308, ry(190, 1)],
    ],
    s.ink,
    1.2,
  )
  line(
    [
      [400, 138],
      [410, 138],
    ],
    s.ink,
    1.2,
  )
  crow(308, ry(190, 1), -1, s.ink)
  tx('SCHEMA · V7', 14, H - 10, 8, s.mut, { mono: 1, w: 600, ls: 1.4 })
  tx('PK primary · FK foreign', W - 14, H - 10, 7.5, s.mut, { mono: 1, al: 'right' })
}
function aCDN(W, H) {
  const s = BP
  sheet(W, H, s, 'EDGE NETWORK')
  const gx = 72,
    gy = 166,
    r = 50
  circ(gx, gy, r, s.fill, s.ink, 1.3)
  c.strokeStyle = s.mut
  c.lineWidth = 1
  ;[0.35, 0.72].forEach((k) => {
    c.beginPath()
    c.ellipse(gx, gy, r * k, r, 0, 0, Math.PI * 2)
    c.stroke()
  })
  line(
    [
      [gx, gy - r],
      [gx, gy + r],
    ],
    s.mut,
    1,
  )
  line(
    [
      [gx - r, gy],
      [gx + r, gy],
    ],
    s.mut,
    1,
  )
  ;[-0.5, 0.5].forEach((k) => {
    const hw = r * Math.sqrt(1 - k * k)
    line(
      [
        [gx - hw, gy + k * r],
        [gx + hw, gy + k * r],
      ],
      s.mut,
      1,
    )
  })
  tx('users', gx, gy + r + 16, 8, s.mut, { al: 'center', mono: 1 })
  ;[
    ['fra', 60, 94],
    ['nyc', 140, 91],
    ['tyo', 220, 88],
  ].forEach(([n, y, hit], i) => {
    curve(gx + r * 0.8, gy + (i - 1) * 20, 170, y + 20, s.ink, { head: 1 })
    box(170, y, 96, 40, 'edge · ' + n, s, { fs: 8.5, mono: 1, sub: `HIT ${hit}%` })
    arrow(
      [
        [266, y + 20],
        [300, y + 20],
        [300, 160],
        [340, 160],
      ],
      s.mut,
      { dash: [3, 3] },
    )
  })
  tx('MISS', 306, 152, 7, s.acc, { mono: 1, w: 600 })
  box(340, 128, 104, 64, 'origin', s, { acc: 1, sub: 'eu-west' })
  arrow(
    [
      [392, 192],
      [392, 228],
    ],
    s.ink,
  )
  cyl(392, 228, 70, 52, 'objects', s)
}

/* ---------- film ---------- */
// 24 slots on the loop; spare frames (swift, clojure, ruby, dGrid, dIcons, aLayers, aER, aCDN) can be swapped in.
export const ORDER = [
  'rust',
  'dMobile',
  'aMicro',
  'python',
  'dDash',
  'go',
  'basic',
  'dLanding',
  'aEvents',
  'ts',
  'dPalette',
  'c',
  'aSeq',
  'haskell',
  'dComponents',
  'asm',
  'aCICD',
  'sql',
  'dLogin',
  'elixir',
  'aK8s',
  'pascal',
  'dKanban',
  'aPipe',
]
const DRAW = {
  dMobile,
  dDash,
  dLanding,
  dPalette,
  dComponents,
  dLogin,
  dKanban,
  dGrid,
  dIcons,
  aMicro,
  aLayers,
  aEvents,
  aSeq,
  aCICD,
  aK8s,
  aPipe,
  aER,
  aCDN,
}
function drawFrame(id, W, H) {
  if (DRAW[id]) return DRAW[id](W, H)
  const f = CODE[id]
  if (id === 'pascal') return turbo(W, H, f)
  if (id === 'basic' || id === 'asm') return crt(W, H, f)
  return editor(W, H, f)
}
function makeGrain() {
  const g = document.createElement('canvas')
  g.width = g.height = 160
  const gc = g.getContext('2d'),
    im = gc.createImageData(160, 160)
  for (let i = 0; i < im.data.length; i += 4) {
    const v = 128 + (Math.random() - 0.5) * 130
    im.data[i] = im.data[i + 1] = im.data[i + 2] = v
    im.data[i + 3] = 255
  }
  gc.putImageData(im, 0, 0)
  return c.createPattern(g, 'repeat')
}
function grade(W, H, r, grain, warm = true) {
  if (warm) {
    c.globalCompositeOperation = 'saturation'
    c.fillStyle = 'rgba(128,128,128,0.16)'
    c.fillRect(0, 0, W, H)
    c.globalCompositeOperation = 'multiply'
    c.fillStyle = 'rgba(255,222,184,0.5)'
    c.fillRect(0, 0, W, H)
    c.globalCompositeOperation = 'screen'
    c.fillStyle = 'rgba(64,34,18,0.2)'
    c.fillRect(0, 0, W, H)
  }
  const g = c.createRadialGradient(W / 2, H / 2, H * 0.35, W / 2, H / 2, W * 0.62)
  g.addColorStop(0, '#ffffff')
  g.addColorStop(1, warm ? '#b4977f' : '#a4a4ac')
  c.globalCompositeOperation = 'multiply'
  c.fillStyle = g
  c.fillRect(0, 0, W, H)
  c.globalCompositeOperation = 'overlay'
  c.globalAlpha = 0.2
  c.fillStyle = grain
  c.fillRect(0, 0, W, H)
  c.globalAlpha = 1
  c.globalCompositeOperation = 'source-over'
  for (let i = 0; i < 6; i++) {
    c.fillStyle = r() < 0.6 ? 'rgba(255,244,226,0.55)' : 'rgba(20,10,5,0.5)'
    c.beginPath()
    c.arc(r() * W, r() * H, 0.5 + r() * 1.2, 0, 7)
    c.fill()
  }
  if (r() < 0.35) {
    c.fillStyle = 'rgba(255,240,220,0.16)'
    c.fillRect(r() * W, 0, 0.8, H)
  }
}
function edges(k, r) {
  const a = 'rgba(226,150,62,0.92)',
    n = String(k + 1)
  tx(n, 46, TH - 9, 10.5, a, { mono: 1, w: 600 })
  tri(250, TH - 17, 250, TH - 9, 257, TH - 13, a)
  tx(n + 'A', 262, TH - 9, 10.5, a, { mono: 1, w: 600 })
  if (k % 4 === 0) tx('SAFETY FILM  8406', 40, 18, 9.5, a, { mono: 1, w: 600, ls: 1.5 })
  else {
    let x = 300
    c.fillStyle = a
    while (x < 450) {
      const w = 1.5 + r() * 3
      c.fillRect(x, 10, w, 8)
      x += w + 1.5 + r() * 3
    }
  }
}
async function loadFonts() {
  const list = [
    '400 12px "IBM Plex Mono"',
    '500 12px "IBM Plex Mono"',
    '600 12px "IBM Plex Mono"',
    'italic 400 12px "IBM Plex Mono"',
    '400 12px "IBM Plex Sans"',
    '500 12px "IBM Plex Sans"',
    '600 12px "IBM Plex Sans"',
    '700 12px "IBM Plex Sans"',
  ]
  try {
    await Promise.race([
      Promise.all(list.map((f) => document.fonts.load(f, 'Aaö·—КАДРЫФСП'))),
      new Promise((r) => setTimeout(r, 4000)),
    ])
  } catch {
    // fonts are optional: frames fall back to system faces
  }
}
export async function drawAtlas() {
  await loadFonts()
  const cv = document.createElement('canvas')
  cv.width = TW * COLS
  cv.height = TH * ROWS
  c = cv.getContext('2d')
  const grain = makeGrain()
  ORDER.forEach((id, k) => {
    const r = rng(k * 977 + 13)
    c.save()
    c.translate((k % COLS) * TW, Math.floor(k / COLS) * TH)
    c.beginPath()
    c.rect(0, 0, TW, TH)
    c.clip()
    const bg = c.createLinearGradient(0, 0, 0, TH)
    bg.addColorStop(0, '#1b120b')
    bg.addColorStop(0.5, '#120b07')
    bg.addColorStop(1, '#1b120b')
    c.fillStyle = bg
    c.fillRect(0, 0, TW, TH)
    c.save()
    c.translate(IX, IY)
    c.beginPath()
    c.roundRect(0, 0, IW, IH, 3)
    c.clip()
    try {
      drawFrame(id, IW, IH)
    } catch (e) {
      console.warn('frame', id, e)
    }
    grade(IW, IH, r, grain)
    c.restore()
    edges(k, r)
    c.globalCompositeOperation = 'destination-out'
    for (let p = 0; p < 8; p++) {
      const x = (p + 0.5) * PP - PA / 2
      rr(x, PE, PA, PX, 4, '#000')
      rr(x, TH - PE - PX, PA, PX, 4, '#000')
    }
    c.globalCompositeOperation = 'source-over'
    c.restore()
  })
  return cv
}

/* ---------- 4-perf motion-picture layout: film runs vertically, x = across, y = along ---------- */
export const CINE = { S: 20, TW: 700, TH: 380, COLS: 5, ROWS: 5 }
// Brand tones: luminance → colour ramp applied to every frame image.
const TONES = {
  kadry: {
    ramp: [
      [0, '#04050c'],
      [0.2, '#0e0c34'],
      [0.42, '#2a1fb8'],
      [0.6, '#4433ff'],
      [0.8, '#aba4ff'],
      [1, '#f5f4ff'],
    ],
    base: ['#0a0b1c', '#05060f'],
    print: '#aba4ff',
    mark: '#4433ff',
    red: '#ff3b4e',
    track: 'rgba(171,164,255,0.38)',
  },
}
const hex = (h) => [1, 3, 5].map((i) => parseInt(h.slice(i, i + 2), 16))
function rampLUT(stops) {
  const lut = new Uint8Array(256 * 3)
  for (let i = 0; i < 256; i++) {
    const v = i / 255
    let k = 0
    while (k < stops.length - 2 && v > stops[k + 1][0]) k++
    const [a, ca] = stops[k],
      [b, cb] = stops[k + 1],
      f = Math.min(1, Math.max(0, (v - a) / (b - a))),
      A = hex(ca),
      B = hex(cb)
    for (let j = 0; j < 3; j++) lut[i * 3 + j] = Math.round(A[j] + (B[j] - A[j]) * f)
  }
  return lut
}
function toneMap(x, y, w, h, lut) {
  const im = c.getImageData(x, y, w, h),
    d = im.data
  for (let i = 0; i < d.length; i += 4) {
    const l = Math.min(255, Math.round(0.2126 * d[i] + 0.7152 * d[i + 1] + 0.0722 * d[i + 2])) * 3
    d[i] = lut[l]
    d[i + 1] = lut[l + 1]
    d[i + 2] = lut[l + 2]
  }
  c.putImageData(im, x, y)
}
function toneEdges(k, r, W, H, t) {
  c.save()
  c.translate(27, H - 36)
  c.rotate(-Math.PI / 2)
  c.font = `600 12px ${MONO}`
  const n = String(k + 1).padStart(2, '0'),
    wb = c.measureText('[ ').width,
    wn = c.measureText(n + ' ').width
  tx('[', 0, 0, 12, t.red, { mono: 1, w: 600 })
  tx(n, wb, 0, 12, t.print, { mono: 1, w: 600 })
  tx(']', wb + wn, 0, 12, t.red, { mono: 1, w: 600 })
  c.restore()
  tri(14, H / 2 - 6, 26, H / 2 - 6, 20, H / 2 + 4, t.print)
  if (k % 4 === 0) {
    c.save()
    c.translate(W - 15, 40)
    c.rotate(Math.PI / 2)
    tx('КАДРЫ · ФСП', 0, 0, 10, t.print, { mono: 1, w: 600, ls: 2 })
    c.restore()
  } else {
    let y = 60
    c.fillStyle = t.mark
    while (y < 300) {
      const h = 1.5 + r() * 3.5
      c.fillRect(W - 30, y, 10, h)
      y += h + 1.5 + r() * 3.5
    }
  }
}
function cineEdges(k, r, W, H) {
  const a = 'rgba(226,150,62,0.92)'
  c.save()
  c.translate(27, H - 40)
  c.rotate(-Math.PI / 2)
  tx(String(k + 1), 0, 0, 12, a, { mono: 1, w: 600 })
  c.restore()
  tri(14, H / 2 - 6, 26, H / 2 - 6, 20, H / 2 + 4, a)
  if (k % 4 === 0) {
    c.save()
    c.translate(W - 15, 40)
    c.rotate(Math.PI / 2)
    tx('SAFETY FILM  8406', 0, 0, 10, a, { mono: 1, w: 600, ls: 1.5 })
    c.restore()
  } else {
    let y = 60
    c.fillStyle = a
    while (y < 300) {
      const h = 1.5 + r() * 3.5
      c.fillRect(W - 30, y, 10, h)
      y += h + 1.5 + r() * 3.5
    }
  }
}
export async function drawCineAtlas(opts = {}) {
  await loadFonts()
  const t = TONES[opts.tone],
    lut = t && rampLUT(t.ramp)
  const { S: s, TW: W, TH: H, COLS: NC, ROWS: NR } = CINE
  const pa = 1.981 * s,
    px = 2.794 * s,
    pe = 2.01 * s,
    pp = 4.75 * s,
    iw = 24 * s,
    ih = 16 * s,
    ix = (W - iw) / 2,
    iy = (H - ih) / 2,
    st = (pe + px + ix) / 2
  const cv = document.createElement('canvas')
  cv.width = W * NC
  cv.height = H * NR
  c = cv.getContext('2d')
  const grain = makeGrain()
  ORDER.forEach((id, k) => {
    const r = rng(k * 977 + 13)
    c.save()
    c.translate((k % NC) * W, Math.floor(k / NC) * H)
    c.beginPath()
    c.rect(0, 0, W, H)
    c.clip()
    const bg = c.createLinearGradient(0, 0, W, 0),
      b0 = t ? t.base[0] : '#1b120b',
      b1 = t ? t.base[1] : '#120b07'
    bg.addColorStop(0, b0)
    bg.addColorStop(0.5, b1)
    bg.addColorStop(1, b0)
    c.fillStyle = bg
    c.fillRect(0, 0, W, H)
    c.fillStyle = t ? t.track : 'rgba(232,196,140,0.45)'
    for (let y = 0; y < H; y++) {
      const g = k * H + y,
        amp = 2.4 + 1.5 * Math.sin(g * 0.13) * Math.sin(g * 0.021) + 0.7 * Math.sin(g * 0.57)
      c.fillRect(st - amp, y, amp * 2, 1)
    }
    c.save()
    c.translate(ix, iy)
    c.beginPath()
    c.roundRect(0, 0, iw, ih, 4)
    c.clip()
    c.scale(iw / IW, ih / IH)
    try {
      drawFrame(id, IW, IH)
    } catch (e) {
      console.warn('frame', id, e)
    }
    grade(IW, IH, r, grain, !t)
    c.restore()
    if (t) {
      const m = c.getTransform()
      toneMap(Math.round(m.e + ix), Math.round(m.f + iy), Math.round(iw), Math.round(ih), lut)
      toneEdges(k, r, W, H, t)
    } else cineEdges(k, r, W, H)
    c.globalCompositeOperation = 'destination-out'
    for (let p = 0; p < 4; p++) {
      const y = (p + 0.5) * pp - pa / 2
      rr(pe, y, px, pa, 5, '#000')
      rr(W - pe - px, y, px, pa, 5, '#000')
    }
    c.globalCompositeOperation = 'source-over'
    c.restore()
  })
  return cv
}
