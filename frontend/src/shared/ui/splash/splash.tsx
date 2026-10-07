import { useEffect } from 'react'

const FADE_MS = 350

let holds = 0

function dismiss() {
  const splash = document.getElementById('splash')
  if (holds > 0 || !splash) return
  splash.classList.add('splash--done')
  window.setTimeout(() => splash.remove(), FADE_MS)
}

function hold() {
  holds += 1
  return () => {
    holds -= 1
    // One gate hands over to the next within a single commit: the cleanup runs before the next
    // mount, so decide only after both have settled.
    window.setTimeout(dismiss, 0)
  }
}

/** Keeps the static splash from index.html on screen while mounted; it fades once nothing holds it. */
export function Splash() {
  useEffect(hold, [])
  return null
}
