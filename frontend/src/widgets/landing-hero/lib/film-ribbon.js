/**
 * A vertical 35mm film strip that enters from the top, curls once and leaves at the
 * bottom, frames flowing continuously. Transparent background: the host element is
 * sized with CSS and the canvas fills it.
 *
 * Ported from the design handoff web component; geometry, light and camera are final.
 */
import * as THREE from 'three'
import { drawCineAtlas, CINE, ORDER } from './reel-frames.js'

const PITCH = 19 / 35,
  SEG = 12,
  VS = 4,
  NT = ORDER.length,
  YAW = -0.85
const ss = (a, b, x) => {
  x = Math.min(1, Math.max(0, (x - a) / (b - a)))
  return x * x * (3 - 2 * x)
}

// Centreline in film-width units: straight drop facing the viewer (view = camera axis in local space), then one forward loop.
function buildPath(view) {
  const [vx, vy, vz] = view
  const r = 0.75,
    t0 = 0.36,
    t1 = 0.64,
    M = 3000,
    ta = -0.15,
    tb = 1.15,
    raw = [],
    rt = []
  for (let i = 0; i < M; i++) {
    const t = ta + ((tb - ta) * i) / (M - 1),
      th = 2 * Math.PI * ss(t0, t1, t)
    rt.push(t)
    raw.push([
      0.7 * Math.sin(Math.PI * (2 * t - 1) * 1.2) + 1.4 * (th / (2 * Math.PI) - 0.5),
      6 - 12 * t - r * Math.sin(th),
      -0.8 + 1.2 * t + r * (1 - Math.cos(th)),
    ])
  }
  const len = [0]
  for (let i = 1; i < M; i++)
    len.push(
      len[i - 1] +
        Math.hypot(raw[i][0] - raw[i - 1][0], raw[i][1] - raw[i - 1][1], raw[i][2] - raw[i - 1][2]),
    )
  const L = len[M - 1],
    K = 2400,
    h = L / (K - 1),
    P = new Float32Array(K * 3),
    T = new Float32Array(K * 3),
    B = new Float32Array(K * 3),
    Tt = new Float32Array(K)
  for (let i = 0, j = 0; i < K; i++) {
    const s = i * h
    while (j < M - 2 && len[j + 1] < s) j++
    const f = (s - len[j]) / (len[j + 1] - len[j] || 1)
    for (let a = 0; a < 3; a++) P[i * 3 + a] = raw[j][a] + (raw[j + 1][a] - raw[j][a]) * f
    Tt[i] = rt[j] + (rt[j + 1] - rt[j]) * f
  }
  let bx = 1,
    by = 0,
    bz = 0
  for (let i = 0; i < K; i++) {
    const i0 = Math.max(0, i - 1) * 3,
      i1 = Math.min(K - 1, i + 1) * 3
    let tx = P[i1] - P[i0],
      ty = P[i1 + 1] - P[i0 + 1],
      tz = P[i1 + 2] - P[i0 + 2]
    const tl = Math.hypot(tx, ty, tz)
    tx /= tl
    ty /= tl
    tz /= tl
    const d = bx * tx + by * ty + bz * tz
    bx -= d * tx
    by -= d * ty
    bz -= d * tz
    const bl = Math.hypot(bx, by, bz)
    bx /= bl
    by /= bl
    bz /= bl
    T.set([tx, ty, tz], i * 3)
    const cx = ty * bz - tz * by,
      cy = tz * bx - tx * bz,
      cz = tx * by - ty * bx
    const fx = vy * tz - vz * ty,
      fy = vz * tx - vx * tz,
      fz = vx * ty - vy * tx
    const t = Tt[i]
    let al = 0
    if (Math.hypot(fx, fy, fz) > 1e-3) {
      al = Math.atan2(fx * cx + fy * cy + fz * cz, fx * bx + fy * by + fz * bz)
      if (al > Math.PI / 2) al -= Math.PI
      else if (al < -Math.PI / 2) al += Math.PI
    }
    const ph = al * (1 - ss(0.35, 0.43, t) * (1 - ss(0.57, 0.65, t))),
      cp = Math.cos(ph),
      sp = Math.sin(ph)
    B.set([bx * cp + cx * sp, by * cp + cy * sp, bz * cp + cz * sp], i * 3)
  }
  return { L, h, K, P, T, B }
}

/**
 * Mounts the ribbon into `host` and returns a dispose function.
 * Options: speed — frames per second (negative runs upward); flip — turn the ribbon
 * upside down (still flows top → bottom); tone — "kadry" recolours frames into the
 * brand indigo ramp; glow — rim-light colour.
 */
const reduce = matchMedia('(prefers-reduced-motion: reduce)')

export function mountFilmRibbon(host, { speed = 0.9, glow = '#ffe2b8', tone, flip = false } = {}) {
  const renderer = new THREE.WebGLRenderer({ antialias: true, alpha: true })
  renderer.setPixelRatio(Math.min(window.devicePixelRatio || 1, 2))
  renderer.setClearColor(0x000000, 0)
  const cv = renderer.domElement
  cv.style.cssText = 'position:absolute;inset:0;width:100%;height:100%;display:block;'
  host.appendChild(cv)

  const cleanup = [
    () => {
      renderer.setAnimationLoop(null)
      renderer.dispose()
      cv.remove()
    },
  ]
  let disposed = false
  const dispose = () => {
    if (disposed) return
    disposed = true
    cleanup.forEach((fn) => fn())
  }

  const boot = async () => {
    const scene = new THREE.Scene()
    const camera = new THREE.OrthographicCamera(-1, 1, 1, -1, 0.1, 200)
    scene.add(new THREE.HemisphereLight(0xfff4e4, 0x1a1830, 1.0))
    const rimColor = new THREE.Color(glow)
    const key = new THREE.DirectionalLight(0xffffff, 2.0)
    key.position.set(-3, 5, 6)
    scene.add(key)
    const rim = new THREE.DirectionalLight(rimColor, 2.2)
    rim.position.set(4, -2, -5)
    scene.add(rim)
    const rim2 = new THREE.DirectionalLight(rimColor, 1.2)
    rim2.position.set(-5, 1, -2)
    scene.add(rim2)

    const atlas = await drawCineAtlas({ tone })
    if (disposed) return
    const tex = new THREE.CanvasTexture(atlas)
    tex.colorSpace = THREE.SRGBColorSpace
    tex.anisotropy = renderer.capabilities.getMaxAnisotropy()

    const view = new THREE.Vector3(0, 0, 1).applyQuaternion(
      new THREE.Quaternion().setFromEuler(new THREE.Euler(0.05, YAW, 0.06)).invert(),
    )
    const { L, h, K, P, T, B } = buildPath(view.toArray())
    const NF = NT * Math.ceil((L / PITCH + 2) / NT),
      span = NF * PITCH
    const nR = VS + 1,
      per = (SEG + 1) * nR,
      N = NF * per,
      AW = CINE.TW * CINE.COLS,
      AH = CINE.TH * CINE.ROWS
    const pos = new Float32Array(N * 3),
      nor = new Float32Array(N * 3),
      uv = new Float32Array(N * 2),
      idx = []
    for (let k = 0; k < NF; k++) {
      const tk = k % NT,
        col = tk % CINE.COLS,
        row = Math.floor(tk / CINE.COLS)
      for (let i = 0; i <= SEG; i++)
        for (let j = 0; j <= VS; j++) {
          const n = k * per + i * nR + j,
            fx = flip ? 1 - i / SEG : i / SEG,
            fy = flip ? 1 - j / VS : j / VS
          uv[n * 2] = ((col + fy) * CINE.TW) / AW
          uv[n * 2 + 1] = 1 - ((row + fx) * CINE.TH) / AH
        }
      for (let i = 0; i < SEG; i++)
        for (let j = 0; j < VS; j++) {
          const a = k * per + i * nR + j,
            d = a + nR
          idx.push(a, d, a + 1, a + 1, d, d + 1)
        }
    }
    const geo = new THREE.BufferGeometry()
    geo.setAttribute('position', new THREE.BufferAttribute(pos, 3))
    geo.setAttribute('normal', new THREE.BufferAttribute(nor, 3))
    geo.setAttribute('uv', new THREE.BufferAttribute(uv, 2))
    geo.setIndex(idx)

    const sample = (s, out) => {
      let i0,
        f,
        ext = 0
      if (s <= 0) {
        i0 = 0
        f = 0
        ext = s
      } else if (s >= L) {
        i0 = K - 2
        f = 1
        ext = s - L
      } else {
        const x = s / h
        i0 = Math.min(K - 2, Math.floor(x))
        f = x - i0
      }
      for (let a = 0; a < 3; a++) {
        const p0 = i0 * 3 + a,
          p1 = p0 + 3
        out[a] = P[p0] + (P[p1] - P[p0]) * f + T[p1] * ext
        out[3 + a] = T[p0] + (T[p1] - T[p0]) * f
        out[6 + a] = B[p0] + (B[p1] - B[p0]) * f
      }
    }
    const o = new Float32Array(9)
    const wind = (offset) => {
      for (let k = 0; k < NF; k++) {
        const s0 = ((((k * PITCH + offset) % span) + span) % span) - PITCH
        for (let i = 0; i <= SEG; i++) {
          sample(s0 + (i / SEG) * PITCH, o)
          const [px, py, pz, tx, ty, tz, bx, by, bz] = o
          let nx = ty * bz - tz * by,
            ny = tz * bx - tx * bz,
            nz = tx * by - ty * bx
          const l = Math.hypot(nx, ny, nz) || 1
          nx /= l
          ny /= l
          nz /= l
          for (let j = 0; j <= VS; j++) {
            const n = (k * per + i * nR + j) * 3,
              v = j / VS - 0.5
            pos[n] = px + bx * v
            pos[n + 1] = py + by * v
            pos[n + 2] = pz + bz * v
            nor[n] = nx
            nor[n + 1] = ny
            nor[n + 2] = nz
          }
        }
      }
      geo.attributes.position.needsUpdate = true
      geo.attributes.normal.needsUpdate = true
    }
    wind(0)
    geo.computeBoundingSphere()

    const mat = new THREE.MeshStandardMaterial({
      map: tex,
      emissive: 0xffffff,
      emissiveMap: tex,
      emissiveIntensity: tone ? 0.45 : 0.32,
      roughness: 0.42,
      metalness: 0,
      alphaTest: 0.5,
      side: THREE.DoubleSide,
    })
    const mesh = new THREE.Mesh(geo, mat)
    mesh.frustumCulled = false
    const group = new THREE.Group()
    group.add(mesh)
    group.rotation.set(0.05, YAW, 0.06)
    const holder = new THREE.Group()
    holder.rotation.z = flip ? Math.PI : 0
    holder.add(group)
    scene.add(holder)
    const base = group.rotation.clone()

    const fit = () => {
      const w = host.clientWidth || 1,
        hh = host.clientHeight || 1,
        asp = w / hh
      renderer.setSize(w, hh, false)
      const half = Math.max(2.4, 2.0 / asp)
      Object.assign(camera, { left: -half * asp, right: half * asp, top: half, bottom: -half })
      camera.position.set(0, 0, 20)
      camera.lookAt(0, 0, 0.2)
      camera.updateProjectionMatrix()
      if (reduce.matches) renderer.render(scene, camera)
    }
    const resize = new ResizeObserver(fit)
    resize.observe(host)
    fit()

    let mx = 0,
      my = 0,
      rx = 0,
      ry = 0
    const onMove = (e) => {
      mx = (e.clientX / innerWidth) * 2 - 1
      my = (e.clientY / innerHeight) * 2 - 1
    }
    window.addEventListener('pointermove', onMove, { passive: true })
    let offset = 0,
      last = performance.now(),
      visible = false
    const tick = (now) => {
      const dt = Math.min(0.05, (now - last) / 1000)
      last = now
      offset += (flip ? -1 : 1) * speed * PITCH * dt
      wind(offset)
      rx += (my - rx) * Math.min(1, dt * 3)
      ry += (mx - ry) * Math.min(1, dt * 3)
      group.rotation.x = base.x + rx * 0.06
      group.rotation.y = base.y + ry * 0.14
      renderer.render(scene, camera)
    }
    // The loop runs only while the ribbon is on screen; with reduced motion it is a still frame.
    const sync = () => {
      if (visible && !reduce.matches) {
        last = performance.now()
        renderer.setAnimationLoop(tick)
      } else {
        renderer.setAnimationLoop(null)
        group.rotation.copy(base)
        renderer.render(scene, camera)
      }
    }
    const inView = new IntersectionObserver(([e]) => {
      visible = e.isIntersecting
      sync()
    })
    inView.observe(host)
    reduce.addEventListener('change', sync)

    cleanup.push(() => {
      resize.disconnect()
      inView.disconnect()
      reduce.removeEventListener('change', sync)
      window.removeEventListener('pointermove', onMove)
      geo.dispose()
      mat.dispose()
      tex.dispose()
    })
  }
  boot().catch((error) => {
    console.warn('film ribbon', error)
    dispose()
  })

  return dispose
}
