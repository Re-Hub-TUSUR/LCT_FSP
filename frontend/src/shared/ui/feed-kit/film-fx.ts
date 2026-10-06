/**
 * WebGL burn-through for the swipe reel: a frame that is skipped chars from one edge, with a
 * glowing rim, a scorched ring and bubbling film ahead of the fire.
 *
 * One long-lived canvas sits over the current frame; `render` draws a state, `clear` wipes it.
 * Without WebGL2 the effect is silently skipped: the strip still moves and the CSS filters stay.
 */

const VERT = `#version 300 es
void main(){vec2 p=vec2(gl_VertexID==1?3.0:-1.0,gl_VertexID==2?3.0:-1.0);gl_Position=vec4(p,0.0,1.0);}`

// Height field `h = 0.9·d + 0.55·fbm`; `e = h − uFront` splits the frame into the hole, the
// white-hot rim, the charred ring and the browned film, see the handoff README.
const FRAG = `#version 300 es
precision highp float;
uniform vec2 uRes;
uniform float uTime, uFront, uSeed;
uniform vec2 uOrigin;
out vec4 o;

float hash(vec2 p){ p=fract(p*vec2(123.34,456.21)+uSeed); p+=dot(p,p+45.32); return fract(p.x*p.y); }
vec2 hash2(vec2 p){ float n=hash(p); return vec2(n,hash(p+n+17.17)); }
float noise(vec2 p){ vec2 i=floor(p),f=fract(p); vec2 u=f*f*(3.0-2.0*f);
  return mix(mix(hash(i),hash(i+vec2(1,0)),u.x),mix(hash(i+vec2(0,1)),hash(i+vec2(1,1)),u.x),u.y); }
float fbm(vec2 p){ float v=0.0,a=0.5; for(int i=0;i<4;i++){ v+=a*noise(p); p=p*2.03+vec2(1.7,9.2); a*=0.5; } return v; }
float cells(vec2 p){ vec2 i=floor(p),f=fract(p); float d=8.0;
  for(int y=-1;y<=1;y++) for(int x=-1;x<=1;x++){ vec2 g=vec2(float(x),float(y)); vec2 r=g+hash2(i+g)-f; d=min(d,dot(r,r)); }
  return sqrt(d); }

void main(){
  vec2 uv=gl_FragCoord.xy/uRes;
  float asp=uRes.x/uRes.y;
  vec2 q=uv*vec2(asp,1.0);
  vec2 w=vec2(fbm(q*1.7+vec2(0.0,uTime*0.06)), fbm(q*1.7+vec2(5.2,1.3)-vec2(uTime*0.05,0.0)));
  float n=fbm(q*2.6+w*1.6);
  float d=length((uv-uOrigin)*vec2(asp,1.0))/(asp+0.6);
  float e=d*0.9+n*0.55-uFront;
  float flick=0.7+0.6*noise(q*16.0+vec2(0.0,-uTime*7.0));
  vec3 col; float a;
  if(e<0.0){
    float fresh=1.0-smoothstep(0.0,0.05,-e);
    float sp=smoothstep(0.72,0.95,noise(q*34.0+vec2(uTime*1.5,-uTime*4.0)));
    col=vec3(0.027,0.035,0.063)+vec3(1.0,0.42,0.08)*sp*fresh*flick*1.6;
    a=1.0;
  } else if(e<0.016){
    col=mix(vec3(1.0,0.96,0.82),vec3(1.0,0.5,0.08),e/0.016)*flick; a=1.0;
  } else if(e<0.07){
    float t=(e-0.016)/0.054;
    col=mix(vec3(0.55,0.12,0.02)*flick,vec3(0.05,0.03,0.025),smoothstep(0.0,0.45,t));
    col=mix(col,vec3(0.16,0.08,0.04),smoothstep(0.6,1.0,t));
    a=1.0;
  } else {
    float t=clamp((e-0.07)/0.17,0.0,1.0);
    col=mix(vec3(0.16,0.08,0.04),vec3(0.42,0.24,0.09),t);
    a=pow(1.0-t,1.6)*0.88;
    float b=cells(q*16.0+w*2.0);
    float bub=1.0-smoothstep(0.0,0.35,t);
    float rim=smoothstep(0.22,0.3,b)*(1.0-smoothstep(0.3,0.38,b));
    col=mix(col,vec3(0.5,0.3,0.12),rim*bub*0.8);
    col*=mix(1.0,0.55,(1.0-smoothstep(0.15,0.3,b))*bub);
  }
  float glow=exp(-max(e,0.0)*22.0)*smoothstep(-0.3,0.02,uFront)*step(0.0,e);
  o=vec4(col*a+vec3(1.0,0.38,0.06)*glow*0.5*flick, a);
}`

const UNIFORMS = ['uRes', 'uTime', 'uFront', 'uSeed', 'uOrigin'] as const

export type BurnState = {
  /** How far the fire has got: about −0.26 (nothing) to 1.45 (the whole frame). */
  front: number
  /** Where it started, in frame coordinates with the y axis up. */
  origin: readonly [number, number]
  /** Seconds, for the flicker. */
  time: number
}

/** The backing store is capped: the shader is heavy and nobody sees the extra pixels. */
export const fxPixelRatio = () =>
  Math.min(window.devicePixelRatio || 1, window.innerWidth < 720 ? 1.25 : 1.5)

function compile(gl: WebGL2RenderingContext, type: number, source: string) {
  const shader = gl.createShader(type)
  if (!shader) return null
  gl.shaderSource(shader, source)
  gl.compileShader(shader)
  if (gl.getShaderParameter(shader, gl.COMPILE_STATUS)) return shader
  console.warn(gl.getShaderInfoLog(shader))
  gl.deleteShader(shader)
  return null
}

export class FilmFX {
  private readonly gl: WebGL2RenderingContext | null = null
  private program: WebGLProgram | null = null
  private vao: WebGLVertexArrayObject | null = null
  private uniforms: Partial<Record<(typeof UNIFORMS)[number], WebGLUniformLocation | null>> = {}
  private dirty = false

  constructor(private readonly canvas: HTMLCanvasElement) {
    // jsdom and old browsers have no WebGL2: the reel works without the fire.
    if (typeof WebGL2RenderingContext === 'undefined') return
    const gl = canvas.getContext('webgl2', {
      alpha: true,
      premultipliedAlpha: true,
      antialias: false,
    })
    if (!gl) return
    const vertex = compile(gl, gl.VERTEX_SHADER, VERT)
    const fragment = compile(gl, gl.FRAGMENT_SHADER, FRAG)
    const program = gl.createProgram()
    if (!vertex || !fragment || !program) return
    gl.attachShader(program, vertex)
    gl.attachShader(program, fragment)
    gl.linkProgram(program)
    if (!gl.getProgramParameter(program, gl.LINK_STATUS)) return
    gl.useProgram(program)
    this.vao = gl.createVertexArray()
    gl.bindVertexArray(this.vao)
    gl.enable(gl.BLEND)
    gl.blendFunc(gl.ONE, gl.ONE_MINUS_SRC_ALPHA)
    for (const name of UNIFORMS) this.uniforms[name] = gl.getUniformLocation(program, name)
    this.gl = gl
    this.program = program
  }

  render({ front, origin, time }: BurnState) {
    const { gl, canvas, uniforms } = this
    if (!gl || !this.program) return
    const ratio = fxPixelRatio()
    const width = Math.max(1, Math.round(canvas.clientWidth * ratio))
    const height = Math.max(1, Math.round(canvas.clientHeight * ratio))
    if (canvas.width !== width || canvas.height !== height) {
      canvas.width = width
      canvas.height = height
    }
    gl.viewport(0, 0, width, height)
    gl.clearColor(0, 0, 0, 0)
    gl.clear(gl.COLOR_BUFFER_BIT)
    gl.uniform2f(uniforms.uRes ?? null, width, height)
    gl.uniform1f(uniforms.uTime ?? null, time)
    gl.uniform1f(uniforms.uFront ?? null, front)
    gl.uniform1f(uniforms.uSeed ?? null, 0.37)
    gl.uniform2f(uniforms.uOrigin ?? null, origin[0], origin[1])
    gl.drawArrays(gl.TRIANGLES, 0, 3)
    this.dirty = true
  }

  clear() {
    if (!this.gl || !this.dirty) return
    this.gl.clearColor(0, 0, 0, 0)
    this.gl.clear(this.gl.COLOR_BUFFER_BIT)
    this.dirty = false
  }

  destroy() {
    if (!this.gl) return
    this.gl.deleteVertexArray(this.vao)
    this.gl.deleteProgram(this.program)
    this.program = null
  }
}
