import { ATLAS_FONTS, FRAME_PITCH, paintAtlas } from './film-atlas'

const FS_VS = `#version 300 es
layout(location=0) in vec2 aPos;
out vec2 vUv;
void main(){ vUv = aPos * 0.5 + 0.5; gl_Position = vec4(aPos, 0.0, 1.0); }`

const STRIP_VS = `#version 300 es
precision highp float;
layout(location=0) in vec2 aPos;
uniform float uTime, uK, uA, uTwist, uTwistF, uWaveY, uDist, uTanH, uAspect;
uniform vec3 uRot;
out float vS; out float vA; out vec3 vN; out vec3 vP;
vec3 path(float s){
  float q = s / uA;
  return vec3(s, uWaveY * sin(s * 0.31 + uTime * 0.06), -uK * uA * (sqrt(1.0 + q * q) - 1.0));
}
mat3 rx(float a){ float c=cos(a), s=sin(a); return mat3(1.,0.,0., 0.,c,s, 0.,-s,c); }
mat3 ry(float a){ float c=cos(a), s=sin(a); return mat3(c,0.,-s, 0.,1.,0., s,0.,c); }
mat3 rz(float a){ float c=cos(a), s=sin(a); return mat3(c,s,0., -s,c,0., 0.,0.,1.); }
void main(){
  float s = aPos.x, a = aPos.y;
  vec3 c = path(s);
  vec3 T = normalize(path(s + 0.02) - path(s - 0.02));
  vec3 U = normalize(vec3(0.,1.,0.) - T * T.y);
  vec3 B = cross(T, U);
  float tw = uTwist * sin(s * uTwistF + uTime * 0.09);
  vec3 up = U * cos(tw) + B * sin(tw);
  vec3 n = cross(T, up);
  vec3 p = c + up * (0.5 - a);
  mat3 R = ry(uRot.x) * rx(uRot.y) * rz(uRot.z);
  p = R * p; n = R * n;
  vec3 v = p - vec3(0., 0., uDist);
  vS = s; vA = a; vN = n; vP = v;
  float f = 1.0 / uTanH;
  float near = 0.05, far = 80.0;
  gl_Position = vec4(v.x * f / uAspect, v.y * f, (v.z * (far + near) + 2.0 * far * near) / (near - far), -v.z);
}`

const STRIP_FS = `#version 300 es
precision highp float;
in float vS; in float vA; in vec3 vN; in vec3 vP;
uniform sampler2D uAtlas;
uniform float uTravel, uPitchU, uFocus, uDof, uSmear;
uniform vec3 uLight;
out vec4 o;
void main(){
  float f = vS / uPitchU + uTravel;
  vec2 g = vec2(f, vA) / 4.0;
  vec2 gx = dFdx(g), gy = dFdy(g);
  vec4 tex = vec4(0.0);
  for (int i = 0; i < 5; i++) {
    float ff = f + uSmear * (float(i) * 0.25 - 0.5);
    float idx = mod(floor(ff), 16.0);
    vec2 cell = vec2(mod(idx, 4.0), floor(idx / 4.0));
    tex += textureGrad(uAtlas, (cell + vec2(fract(ff), vA)) / 4.0, gx, gy);
  }
  tex *= 0.2;
  vec3 V = normalize(-vP);
  vec3 N = normalize(vN);
  N = faceforward(N, -V, N);
  float ndv = clamp(dot(N, V), 0.0, 1.0);
  float hole = 1.0 - tex.a;
  vec3 col = tex.rgb * (0.62 + 0.38 * ndv) * 1.12 + vec3(0.72, 0.76, 0.88) * (0.4 + 0.6 * ndv) * hole;
  vec3 H = normalize(normalize(uLight) + V);
  float nh = max(dot(N, H), 0.0);
  float spec = pow(nh, 160.0) * 0.8 + pow(nh, 22.0) * 0.07;
  float fres = pow(1.0 - ndv, 5.0) * 0.4;
  col += (spec + fres) * (1.0 - hole) * vec3(0.88, 0.92, 1.0);
  float e = min(vA, 1.0 - vA);
  col += smoothstep(0.012, 0.0, e) * (0.05 + spec * 1.5);
  float coc = clamp(abs(-vP.z - uFocus) * uDof, 0.0, 1.0);
  o = vec4(col, coc);
}`

const BG_FS = `#version 300 es
precision highp float;
in vec2 vUv;
uniform float uAspect;
out vec4 o;
void main(){
  vec2 p = (vUv - 0.5) * vec2(uAspect, 1.0);
  float g = exp(-(p.x * p.x * 0.9 + p.y * p.y * 7.0));
  float g2 = exp(-dot(p, p) * 0.8);
  vec3 c = vec3(0.011, 0.011, 0.016) + vec3(0.02, 0.0, 0.17) * g + vec3(0.01, 0.012, 0.028) * g2;
  o = vec4(c, 0.0);
}`

const DOWN_FS = `#version 300 es
precision highp float;
in vec2 vUv;
uniform sampler2D uSrc; uniform vec2 uTexel;
out vec4 o;
void main(){
  vec2 d = uTexel;
  o = 0.25 * (texture(uSrc, vUv + vec2(-d.x, -d.y)) + texture(uSrc, vUv + vec2(d.x, -d.y)) + texture(uSrc, vUv + vec2(-d.x, d.y)) + texture(uSrc, vUv + vec2(d.x, d.y)));
}`

const BLUR_FS = `#version 300 es
precision highp float;
in vec2 vUv;
uniform sampler2D uSrc; uniform vec2 uDir;
out vec4 o;
void main(){
  vec4 s = texture(uSrc, vUv) * 0.2270270270;
  s += (texture(uSrc, vUv + uDir * 1.3846153846) + texture(uSrc, vUv - uDir * 1.3846153846)) * 0.3162162162;
  s += (texture(uSrc, vUv + uDir * 3.2307692308) + texture(uSrc, vUv - uDir * 3.2307692308)) * 0.0702702703;
  o = s;
}`

const COMP_FS = `#version 300 es
precision highp float;
in vec2 vUv;
uniform sampler2D uA, uB, uC, uD;
uniform float uTime;
out vec4 o;
vec3 dof(vec2 uv){
  vec4 a = texture(uA, uv), b = texture(uB, uv), c = texture(uC, uv), d = texture(uD, uv);
  float k = max(a.a, max(b.a * 1.1, max(c.a, d.a)));
  vec3 col = mix(a.rgb, b.rgb, smoothstep(0.0, 0.3, k));
  col = mix(col, c.rgb, smoothstep(0.25, 0.6, k));
  col = mix(col, d.rgb, smoothstep(0.55, 1.0, k));
  col += max(d.rgb - 0.16, 0.0) * 0.5 + max(c.rgb - 0.3, 0.0) * 0.2;
  return col;
}
float hash(vec2 p){ p = fract(p * vec2(123.34, 456.21)); p += dot(p, p + 45.32); return fract(p.x * p.y); }
void main(){
  vec2 uv = vUv;
  float burst = smoothstep(0.94, 0.995, sin(uTime * 6.28318 / 7.0));
  float band = step(0.88, fract(uv.y * 13.0 + floor(uTime * 10.0) * 0.618));
  uv.x += burst * band * 0.005;
  vec2 cc = uv - 0.5;
  vec2 off = cc * 0.004 + vec2(burst * 0.002, 0.0);
  vec3 col = vec3(dof(uv + off).r, dof(uv).g, dof(uv - off).b);
  float lum = dot(col, vec3(0.299, 0.587, 0.114));
  float n = hash(gl_FragCoord.xy + fract(uTime * 7.13) * 917.0) - 0.5;
  col += n * (0.03 + lum * 0.08);
  col *= 1.0 - 0.42 * smoothstep(0.35, 0.95, length(cc * vec2(1.0, 0.85)) * 1.2);
  o = vec4(col, 1.0);
}`

// Strip height in world units is 1; `f` is the share of the viewport height the in-focus strip takes
const CAMERA = {
  f: 0.6,
  yaw: 0.5,
  pitch: -0.16,
  roll: 0.02,
  K: 0.04,
  A: 3.0,
  twist: 0.04,
  twistF: 0.3,
  waveY: 0.02,
  dof: 1.0,
  breath: 0.04,
  rack: 0.25,
}
const TAN_HALF_FOV = Math.tan((30 * Math.PI) / 360)
const SEGMENTS = 420
const HALF_LENGTH = 11
const MAX_DPR = 1.25
const FRAMES_PER_SECTION = 4

type Program = {
  handle: WebGLProgram
  locs: Map<string, WebGLUniformLocation | null>
}

type Target = {
  tex: WebGLTexture | null
  fb: WebGLFramebuffer | null
  w: number
  h: number
}

type Targets = {
  ms: WebGLFramebuffer | null
  color: WebGLRenderbuffer | null
  depth: WebGLRenderbuffer | null
  A: Target
  B0: Target
  B1: Target
  C0: Target
  C1: Target
  D0: Target
  D1: Target
}

export type FilmRenderer = {
  render: (now: number) => void
  destroy: () => void
}

/**
 * Film strip in perspective with depth of field: scene → MSAA buffer → blur pyramid → composite.
 * Returns null when WebGL2 is unavailable.
 */
export function createFilmRenderer(
  canvas: HTMLCanvasElement,
  host: HTMLElement,
): FilmRenderer | null {
  const gl = canvas.getContext('webgl2', {
    alpha: false,
    antialias: false,
    depth: false,
    premultipliedAlpha: false,
    powerPreference: 'high-performance',
  })
  if (!gl) return null

  const strip = createProgram(gl, STRIP_VS, STRIP_FS)
  const bg = createProgram(gl, FS_VS, BG_FS)
  const down = createProgram(gl, FS_VS, DOWN_FS)
  const blur = createProgram(gl, FS_VS, BLUR_FS)
  const comp = createProgram(gl, FS_VS, COMP_FS)
  const programs = [strip, bg, down, blur, comp]
  if (!strip || !bg || !down || !blur || !comp) {
    for (const program of programs) if (program) gl.deleteProgram(program.handle)
    return null
  }

  const loc = (program: Program, name: string) => {
    let found = program.locs.get(name)
    if (found === undefined) {
      found = gl.getUniformLocation(program.handle, name)
      program.locs.set(name, found)
    }
    return found
  }

  const meshData = new Float32Array((SEGMENTS + 1) * 4)
  for (let i = 0; i <= SEGMENTS; i += 1) {
    const s = -HALF_LENGTH + (2 * HALF_LENGTH * i) / SEGMENTS
    meshData.set([s, 0, s, 1], i * 4)
  }
  const mesh = createGeometry(gl, meshData)
  const triangle = createGeometry(gl, new Float32Array([-1, -1, 3, -1, -1, 3]))

  let alive = true
  const atlas = gl.createTexture()
  const aniso = gl.getExtension('EXT_texture_filter_anisotropic')
  const uploadAtlas = () => {
    const source = paintAtlas()
    if (!source) return
    gl.bindTexture(gl.TEXTURE_2D, atlas)
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, true)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA, gl.RGBA, gl.UNSIGNED_BYTE, source)
    gl.pixelStorei(gl.UNPACK_PREMULTIPLY_ALPHA_WEBGL, false)
    gl.generateMipmap(gl.TEXTURE_2D)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR_MIPMAP_LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    if (aniso) {
      const max = gl.getParameter(aniso.MAX_TEXTURE_MAX_ANISOTROPY_EXT) as number
      gl.texParameterf(gl.TEXTURE_2D, aniso.TEXTURE_MAX_ANISOTROPY_EXT, Math.min(8, max))
    }
  }
  uploadAtlas()
  // First paint may fall back to a system monospace; repaint once the real face is in
  if (document.fonts) {
    void Promise.all(ATLAS_FONTS.map((font) => document.fonts.load(font)))
      .then(() => {
        if (alive) uploadAtlas()
      })
      .catch(() => {})
  }

  const createTarget = (w: number, h: number): Target => {
    const tex = gl.createTexture()
    gl.bindTexture(gl.TEXTURE_2D, tex)
    gl.texImage2D(gl.TEXTURE_2D, 0, gl.RGBA8, w, h, 0, gl.RGBA, gl.UNSIGNED_BYTE, null)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MIN_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_MAG_FILTER, gl.LINEAR)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_S, gl.CLAMP_TO_EDGE)
    gl.texParameteri(gl.TEXTURE_2D, gl.TEXTURE_WRAP_T, gl.CLAMP_TO_EDGE)
    const fb = gl.createFramebuffer()
    gl.bindFramebuffer(gl.FRAMEBUFFER, fb)
    gl.framebufferTexture2D(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.TEXTURE_2D, tex, 0)
    return { tex, fb, w, h }
  }

  let targets: Targets | null = null
  const freeTargets = () => {
    if (!targets) return
    const { ms, color, depth, ...levels } = targets
    for (const level of Object.values(levels)) {
      gl.deleteTexture(level.tex)
      gl.deleteFramebuffer(level.fb)
    }
    gl.deleteRenderbuffer(color)
    gl.deleteRenderbuffer(depth)
    gl.deleteFramebuffer(ms)
    targets = null
  }

  const samples = Math.min(4, (gl.getParameter(gl.MAX_SAMPLES) as number) || 0)
  const allocate = (w: number, h: number): Targets => {
    freeTargets()
    const ms = gl.createFramebuffer()
    gl.bindFramebuffer(gl.FRAMEBUFFER, ms)
    const color = gl.createRenderbuffer()
    gl.bindRenderbuffer(gl.RENDERBUFFER, color)
    gl.renderbufferStorageMultisample(gl.RENDERBUFFER, samples, gl.RGBA8, w, h)
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.COLOR_ATTACHMENT0, gl.RENDERBUFFER, color)
    const depth = gl.createRenderbuffer()
    gl.bindRenderbuffer(gl.RENDERBUFFER, depth)
    gl.renderbufferStorageMultisample(gl.RENDERBUFFER, samples, gl.DEPTH_COMPONENT16, w, h)
    gl.framebufferRenderbuffer(gl.FRAMEBUFFER, gl.DEPTH_ATTACHMENT, gl.RENDERBUFFER, depth)
    const level = (divisor: number) =>
      createTarget(Math.max(1, Math.round(w / divisor)), Math.max(1, Math.round(h / divisor)))
    return {
      ms,
      color,
      depth,
      A: createTarget(w, h),
      B0: level(2),
      B1: level(2),
      C0: level(4),
      C1: level(4),
      D0: level(8),
      D1: level(8),
    }
  }

  const resize = () => {
    const dpr = Math.min(window.devicePixelRatio || 1, MAX_DPR)
    const w = Math.max(2, Math.floor(host.clientWidth * dpr))
    const h = Math.max(2, Math.floor(host.clientHeight * dpr))
    if (!targets || canvas.width !== w || canvas.height !== h) {
      canvas.width = w
      canvas.height = h
      targets = allocate(w, h)
    }
    return targets
  }

  const fullscreen = (program: Program, target: Target | null) => {
    gl.bindFramebuffer(gl.FRAMEBUFFER, target ? target.fb : null)
    gl.viewport(0, 0, target ? target.w : canvas.width, target ? target.h : canvas.height)
    gl.useProgram(program.handle)
    gl.bindVertexArray(triangle.vao)
    gl.drawArrays(gl.TRIANGLES, 0, 3)
  }
  const bindTexture = (program: Program, name: string, unit: number, tex: WebGLTexture | null) => {
    gl.activeTexture(gl.TEXTURE0 + unit)
    gl.bindTexture(gl.TEXTURE_2D, tex)
    gl.uniform1i(loc(program, name), unit)
  }
  const downsample = (from: Target, to: Target) => {
    gl.useProgram(down.handle)
    bindTexture(down, 'uSrc', 0, from.tex)
    gl.uniform2f(loc(down, 'uTexel'), 1 / from.w, 1 / from.h)
    fullscreen(down, to)
  }
  const gauss = (a: Target, b: Target, spread: number) => {
    gl.useProgram(blur.handle)
    bindTexture(blur, 'uSrc', 0, a.tex)
    gl.uniform2f(loc(blur, 'uDir'), spread / a.w, 0)
    fullscreen(blur, b)
    bindTexture(blur, 'uSrc', 0, b.tex)
    gl.uniform2f(loc(blur, 'uDir'), 0, spread / b.h)
    fullscreen(blur, a)
  }

  let last = performance.now()
  let time = 0
  let lastTravel: number | null = null
  let smoothed = window.scrollY / (window.innerHeight || 1)
  let prevProgress = smoothed
  let velocity = 0

  const render = (now: number) => {
    if (!alive) return
    const dt = Math.min(0.05, Math.max(0, (now - last) / 1000))
    last = now
    time += dt
    const T = resize()

    const progress = window.scrollY / (window.innerHeight || 1)
    smoothed += (progress - smoothed) * (1 - Math.exp(-dt * 5))
    const rawVelocity = dt > 0 ? (progress - prevProgress) / dt : 0
    prevProgress = progress
    velocity += (rawVelocity - velocity) * (1 - Math.exp(-dt * 4))

    const W = canvas.width
    const H = canvas.height
    const aspect = W / H
    const f = aspect < 0.95 ? CAMERA.f * 0.62 : CAMERA.f
    const distance = 1 / (2 * f * TAN_HALF_FOV)
    const yaw = CAMERA.yaw + 0.02 * Math.sin(time * 0.11)
    const pitch = CAMERA.pitch + 0.012 * Math.sin(time * 0.083 + 1)
    const focus =
      distance +
      CAMERA.breath * Math.sin(time * 0.37) +
      clamp(velocity * 0.3, -0.5, 0.5) * CAMERA.rack

    // Slow drift + 4 frames per section, direction alternates by chapter
    const leg = Math.floor(smoothed)
    const along = smoothed - leg
    const amount = leg % 2 === 0 ? along : 1 - along
    const travel = time * 0.12 + amount * FRAMES_PER_SECTION
    const smear = lastTravel === null ? 0 : clamp((travel - lastTravel) * 0.6, -0.15, 0.15)
    lastTravel = travel

    // scene → multisampled buffer, alpha carries the circle of confusion
    gl.bindFramebuffer(gl.FRAMEBUFFER, T.ms)
    gl.viewport(0, 0, W, H)
    gl.disable(gl.BLEND)
    gl.clearColor(0, 0, 0, 0)
    gl.clearDepth(1)
    gl.depthMask(true)
    gl.clear(gl.COLOR_BUFFER_BIT | gl.DEPTH_BUFFER_BIT)
    gl.disable(gl.DEPTH_TEST)
    gl.depthMask(false)
    gl.useProgram(bg.handle)
    gl.uniform1f(loc(bg, 'uAspect'), aspect)
    gl.bindVertexArray(triangle.vao)
    gl.drawArrays(gl.TRIANGLES, 0, 3)

    gl.enable(gl.DEPTH_TEST)
    gl.depthMask(true)
    gl.disable(gl.CULL_FACE)
    gl.useProgram(strip.handle)
    gl.uniform1f(loc(strip, 'uTime'), time)
    gl.uniform1f(loc(strip, 'uK'), CAMERA.K)
    gl.uniform1f(loc(strip, 'uA'), CAMERA.A)
    gl.uniform1f(loc(strip, 'uSmear'), smear)
    gl.uniform1f(loc(strip, 'uTwist'), CAMERA.twist)
    gl.uniform1f(loc(strip, 'uTwistF'), CAMERA.twistF)
    gl.uniform1f(loc(strip, 'uWaveY'), CAMERA.waveY)
    gl.uniform1f(loc(strip, 'uDist'), distance)
    gl.uniform1f(loc(strip, 'uTanH'), TAN_HALF_FOV)
    gl.uniform1f(loc(strip, 'uAspect'), aspect)
    gl.uniform3f(loc(strip, 'uRot'), yaw, pitch, CAMERA.roll)
    gl.uniform1f(loc(strip, 'uTravel'), travel)
    gl.uniform1f(loc(strip, 'uPitchU'), FRAME_PITCH)
    gl.uniform1f(loc(strip, 'uFocus'), focus)
    gl.uniform1f(loc(strip, 'uDof'), CAMERA.dof)
    gl.uniform3f(loc(strip, 'uLight'), -0.55, 0.7, 0.6)
    bindTexture(strip, 'uAtlas', 0, atlas)
    gl.bindVertexArray(mesh.vao)
    gl.drawArrays(gl.TRIANGLE_STRIP, 0, (SEGMENTS + 1) * 2)
    gl.disable(gl.DEPTH_TEST)

    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, T.ms)
    gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, T.A.fb)
    gl.blitFramebuffer(0, 0, W, H, 0, 0, W, H, gl.COLOR_BUFFER_BIT, gl.NEAREST)
    gl.bindFramebuffer(gl.READ_FRAMEBUFFER, null)
    gl.bindFramebuffer(gl.DRAW_FRAMEBUFFER, null)

    // blur pyramid
    downsample(T.A, T.B0)
    gauss(T.B0, T.B1, 1)
    downsample(T.B0, T.C0)
    gauss(T.C0, T.C1, 1)
    downsample(T.C0, T.D0)
    gauss(T.D0, T.D1, 1)
    gauss(T.D0, T.D1, 1.6)

    gl.useProgram(comp.handle)
    bindTexture(comp, 'uA', 0, T.A.tex)
    bindTexture(comp, 'uB', 1, T.B0.tex)
    bindTexture(comp, 'uC', 2, T.C0.tex)
    bindTexture(comp, 'uD', 3, T.D0.tex)
    gl.uniform1f(loc(comp, 'uTime'), time)
    fullscreen(comp, null)
  }

  return {
    render,
    // Resources are freed by hand: losing the context would leave the canvas dead on remount
    destroy() {
      alive = false
      freeTargets()
      gl.deleteTexture(atlas)
      for (const geometry of [mesh, triangle]) {
        gl.deleteVertexArray(geometry.vao)
        gl.deleteBuffer(geometry.buffer)
      }
      for (const program of [strip, bg, down, blur, comp]) gl.deleteProgram(program.handle)
    },
  }
}

function clamp(value: number, min: number, max: number) {
  return Math.min(max, Math.max(min, value))
}

function createGeometry(gl: WebGL2RenderingContext, data: Float32Array) {
  const vao = gl.createVertexArray()
  gl.bindVertexArray(vao)
  const buffer = gl.createBuffer()
  gl.bindBuffer(gl.ARRAY_BUFFER, buffer)
  gl.bufferData(gl.ARRAY_BUFFER, data, gl.STATIC_DRAW)
  gl.enableVertexAttribArray(0)
  gl.vertexAttribPointer(0, 2, gl.FLOAT, false, 0, 0)
  gl.bindVertexArray(null)
  return { vao, buffer }
}

function createProgram(gl: WebGL2RenderingContext, vertex: string, fragment: string) {
  const vert = compile(gl, gl.VERTEX_SHADER, vertex)
  const frag = compile(gl, gl.FRAGMENT_SHADER, fragment)
  if (!vert || !frag) return null
  const handle = gl.createProgram()
  if (!handle) return null
  gl.attachShader(handle, vert)
  gl.attachShader(handle, frag)
  gl.linkProgram(handle)
  gl.deleteShader(vert)
  gl.deleteShader(frag)
  if (!gl.getProgramParameter(handle, gl.LINK_STATUS)) return null
  const program: Program = { handle, locs: new Map() }
  return program
}

function compile(gl: WebGL2RenderingContext, type: number, source: string) {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (!gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return null
  return shader
}
