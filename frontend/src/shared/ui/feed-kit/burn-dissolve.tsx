import { useEffect, useRef } from 'react'

const BURN_MS = 900

const VERT = `#version 300 es
void main() {
  vec2 p = vec2(gl_VertexID == 1 ? 3.0 : -1.0, gl_VertexID == 2 ? 3.0 : -1.0);
  gl_Position = vec4(p, 0.0, 1.0);
}
`

const FRAG = `#version 300 es
precision highp float;
uniform float uTime;
uniform vec2 uRes;
out vec4 fragColor;

float hash(vec2 p) {
  return fract(sin(dot(p, vec2(127.1, 311.7))) * 43758.5453123);
}

float noise(vec2 p) {
  vec2 i = floor(p);
  vec2 f = fract(p);
  float a = hash(i);
  float b = hash(i + vec2(1.0, 0.0));
  float c = hash(i + vec2(0.0, 1.0));
  float d = hash(i + vec2(1.0, 1.0));
  vec2 u = f * f * (3.0 - 2.0 * f);
  return mix(mix(a, b, u.x), mix(c, d, u.x), u.y);
}

float fbm(vec2 p) {
  float v = 0.0;
  float a = 0.5;
  for (int i = 0; i < 5; i++) {
    v += a * noise(p);
    p = p * 2.02 + vec2(1.7, 9.2);
    a *= 0.5;
  }
  return v;
}

void main() {
  vec2 uv = gl_FragCoord.xy / uRes;
  float height = fbm(uv * 3.4) * 0.7 + uv.y * 0.3;
  float edgeWidth = 0.055;

  if (height > uTime + edgeWidth) {
    fragColor = vec4(0.0);
    return;
  }

  if (height < uTime) {
    vec3 ash = vec3(0.063, 0.071, 0.110);
    float ember = step(0.86, noise(uv * 22.0 + vec2(0.0, uTime * 6.0)));
    float fresh = 1.0 - smoothstep(0.0, 0.18, uTime - height);
    ash = mix(ash, vec3(1.0, 0.42, 0.06), ember * fresh);
    fragColor = vec4(ash, 1.0);
    return;
  }

  float t = (height - uTime) / edgeWidth;
  vec3 hot = vec3(1.0, 0.9, 0.4);
  vec3 mid = vec3(1.0, 0.42, 0.05);
  vec3 cool = vec3(0.55, 0.07, 0.0);
  vec3 burn = t < 0.45 ? mix(hot, mid, t / 0.45) : mix(mid, cool, (t - 0.45) / 0.55);
  float alpha = 1.0 - smoothstep(0.62, 1.0, t);
  fragColor = vec4(burn, alpha);
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

/**
 * Dissolve with a burning edge, the same idea as the PlayCanvas custom-shader
 * tutorial: a height field eats the card, and the threshold glows yellow to orange.
 * The height is procedural, because the card is HTML rather than a mesh texture.
 */
export function BurnDissolve() {
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
    const bindProgram = gl.useProgram.bind(gl)
    bindProgram(program)
    const mesh = gl.createVertexArray()
    if (mesh) gl.bindVertexArray(mesh)
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.SRC_ALPHA, gl.ONE_MINUS_SRC_ALPHA)

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
      const linear = Math.min(1, (now - started) / BURN_MS)
      const eased = linear * linear * (3 - 2 * linear)
      draw(eased * 1.2)
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

  return <canvas ref={ref} className="reel__burn" aria-hidden />
}
