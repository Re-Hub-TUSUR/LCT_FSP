export type FilmRibbonOptions = {
  /** Frames per second; negative runs upward. */
  speed?: number
  /** Rim-light colour. */
  glow?: string
  /** Recolours frames into a brand ramp. */
  tone?: 'kadry'
  /** Turns the ribbon upside down; it still flows top → bottom. */
  flip?: boolean
}

/** Mounts the WebGL ribbon into `host`; returns a dispose function. Throws if WebGL is unavailable. */
export function mountFilmRibbon(host: HTMLElement, options?: FilmRibbonOptions): () => void
