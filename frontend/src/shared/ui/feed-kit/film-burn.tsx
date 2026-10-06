import { useEffect, useRef } from 'react'

/** Runs for the whole rewind, so the light leak eases in and out instead of flashing. */
const FILM_BURN_MS = 1080

const VERT = `#version 300 es
void main() {
  vec2 p = vec2(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0);
  gl_Position = vec4(p, 0.0, 1.0);
}
`

// Light-leak math from the FilmBurn GL transition.
// Author: Anastasia Dunbar. License: MIT.
// https://gl-transitions.com/editor/FilmBurn
const FRAG = `#version 300 es
precision highp float;
uniform float uTime;
uniform vec2 uRes;
uniform float uSeed;
out vec4 fragColor;

#define PI 3.14159265358979323
#define CLAMPS(x) clamp(x, 0.0, 1.0)

float sigmoid(float x, float a) {
  float b = pow(x * 2.0, a) / 2.0;
  if (x > 0.5) {
    b = 1.0 - pow(2.0 - (x * 2.0), a) / 2.0;
  }
  return b;
}

float rand(float co) {
  return fract(sin((co * 24.9898) + uSeed) * 43758.5453);
}

float apow(float a, float b) {
  return pow(abs(a), b) * sign(b);
}

vec3 pow3(vec3 a, vec3 b) {
  return vec3(apow(a.r, b.r), apow(a.g, b.g), apow(a.b, b.b));
}

float smoothMix(float a, float b, float c) {
  return mix(a, b, sigmoid(c, 2.0));
}

float random(vec2 co, float shft) {
  co += 10.0;
  return smoothMix(
    fract(sin(dot(co.xy, vec2(12.9898 + (floor(shft) * 0.5), 78.233 + uSeed))) * 43758.5453),
    fract(sin(dot(co.xy, vec2(12.9898 + (floor(shft + 1.0) * 0.5), 78.233 + uSeed))) * 43758.5453),
    fract(shft)
  );
}

float smoothRandom(vec2 co, float shft) {
  return smoothMix(
    smoothMix(random(floor(co), shft), random(floor(co + vec2(1.0, 0.0)), shft), fract(co.x)),
    smoothMix(random(floor(co + vec2(0.0, 1.0)), shft), random(floor(co + vec2(1.0, 1.0)), shft), fract(co.x)),
    fract(co.y)
  );
}

vec3 leaks(vec2 p, float progress) {
  vec3 f = vec3(0.0);
  for (float i = 0.0; i < 13.0; i++) {
    f += sin(((p.x * rand(i) * 6.0) + (progress * 8.0)) + rand(i + 1.43))
      * sin(((p.y * rand(i + 4.4) * 6.0) + (progress * 6.0)) + rand(i + 2.4));
    f += 1.0 - CLAMPS(length(p - vec2(
      smoothRandom(vec2(progress * 1.3), i + 1.0),
      smoothRandom(vec2(progress * 0.5), i + 6.25)
    )) * mix(20.0, 70.0, rand(i)));
  }
  f += 4.0;
  f /= 11.0;
  f = pow3(f * vec3(1.0, 0.7, 0.6), vec3(1.0, 2.0 - sin(progress * PI), 1.3));
  f *= sin(progress * PI);
  return f;
}

void main() {
  float progress = clamp(uTime, 0.0, 1.0);
  vec2 p = gl_FragCoord.xy / uRes;
  vec3 f = leaks(p, progress);
  float hot = clamp(max(f.r, max(f.g, f.b)), 0.0, 1.0);
  // Peaks while the card is still in the gate, then eases out as it leaves.
  float envelope = sin(clamp(progress * 1.35, 0.0, 1.0) * PI);
  envelope = envelope * envelope * (3.0 - 2.0 * envelope);
  float wash = smoothstep(1.05, 0.12, length((p - vec2(0.42, 0.4)) * vec2(1.15, 1.0)));
  vec3 amber = vec3(1.0, 0.62, 0.22);
  vec3 core = vec3(1.0, 0.94, 0.62);
  vec3 color = mix(amber, core, clamp(hot * 1.4, 0.0, 1.0));
  float alpha = envelope * (0.62 * wash + 0.95 * hot);
  fragColor = vec4(color, clamp(alpha, 0.0, 0.88));
}
`

function compile(gl: WebGL2RenderingContext, type: number, source: string) {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) {
    gl.deleteShader(shader)
    return null
  }
  return shader
}

/** Soft film-burn light leak over the card sent to «Интересно». */
export function FilmBurn() {
  const ref = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = ref.current
    if (!canvas) return
    const gl = canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: false,
      antialias: false,
    })
    if (!gl) return

    const vert = compile(gl, gl.VERTEX_SHADER, VERT)
    const frag = compile(gl, gl.FRAGMENT_SHADER, FRAG)
    if (!vert || !frag) return
    const program = gl.createProgram()
    if (!program) return
    gl.attachShader(program, vert)
    gl.attachShader(program, frag)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return

    const uTime = gl.getUniformLocation(program, 'uTime')
    const uRes = gl.getUniformLocation(program, 'uRes')
    const uSeed = gl.getUniformLocation(program, 'uSeed')
    const bindProgram = gl.useProgram.bind(gl)
    bindProgram(program)
    const mesh = gl.createVertexArray()
    if (mesh) gl.bindVertexArray(mesh)
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)
    gl.uniform1f(uSeed, 2.31)

    const resize = () => {
      const rect = canvas.getBoundingClientRect()
      const dpr = Math.min(window.devicePixelRatio || 1, 2)
      const width = Math.max(1, Math.round(rect.width * dpr))
      const height = Math.max(1, Math.round(rect.height * dpr))
      if (canvas.width !== width || canvas.height !== height) {
        canvas.width = width
        canvas.height = height
      }
    }

    const draw = (time: number) => {
      resize()
      gl.viewport(0, 0, canvas.width, canvas.height)
      gl.clearColor(0, 0, 0, 0)
      gl.clear(gl.COLOR_BUFFER_BIT)
      gl.uniform1f(uTime, time)
      gl.uniform2f(uRes, canvas.width, canvas.height)
      gl.drawArrays(gl.TRIANGLES, 0, 3)
    }

    const started = performance.now()
    let frame = 0
    const tick = (now: number) => {
      const linear = Math.min(1, (now - started) / FILM_BURN_MS)
      draw(linear)
      if (linear < 1) frame = requestAnimationFrame(tick)
    }
    frame = requestAnimationFrame(tick)

    return () => {
      cancelAnimationFrame(frame)
      if (mesh) gl.deleteVertexArray(mesh)
      gl.deleteProgram(program)
      gl.deleteShader(vert)
      gl.deleteShader(frag)
    }
  }, [])

  return <canvas ref={ref} className="reel__film" aria-hidden />
}
