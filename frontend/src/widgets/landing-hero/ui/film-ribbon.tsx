import { useEffect, useRef } from 'react'
import { RIBBON } from '../config/content'

/** Decorative 3D film strip. three.js is loaded lazily so it never blocks the signup form. */
export function FilmRibbon() {
  const hostRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const host = hostRef.current
    if (!host || !('WebGLRenderingContext' in window)) return

    let cancelled = false
    let dispose: (() => void) | undefined

    import('../lib/film-ribbon.js')
      .then(({ mountFilmRibbon }) => {
        if (!cancelled) dispose = mountFilmRibbon(host, RIBBON)
      })
      .catch((error: unknown) => {
        // Purely decorative: without WebGL the hero keeps its glow background.
        console.warn('film ribbon', error)
      })

    return () => {
      cancelled = true
      dispose?.()
    }
  }, [])

  return <div ref={hostRef} className="hero__ribbon" aria-hidden="true" />
}
