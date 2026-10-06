import { useEffect, useRef } from 'react'
import { createFilmRenderer } from '../lib/film-renderer'
import './film-glitch.css'

type Props = {
  poster: string
}

/**
 * A looping film strip of code stills, shot in macro: perspective, depth of field, quiet glitch.
 * Scroll pulls the strip four frames per section, direction alternates by chapter.
 */
export function FilmGlitch(_props: Props) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  useEffect(() => {
    const canvas = canvasRef.current
    const parent = canvas?.parentElement
    if (!canvas || !parent) return
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return

    const renderer = createFilmRenderer(canvas, parent)
    if (!renderer) return

    let frame = 0
    let running = true
    let onScreen = false

    const draw = (now: number) => {
      if (!running || !onScreen) return
      renderer.render(now)
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

    return () => {
      running = false
      cancelAnimationFrame(frame)
      visibility.disconnect()
      renderer.destroy()
    }
  }, [])

  return <canvas ref={canvasRef} className="film-glitch" aria-hidden="true" />
}
