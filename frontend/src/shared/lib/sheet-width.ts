import { useLayoutEffect, useRef, useState } from 'react'

const NARROW = 40
const WIDE = 70

function contentFits(panel: HTMLElement) {
  return Array.from(panel.querySelectorAll<HTMLElement>('[data-fit]')).every(
    (node) => node.scrollHeight <= node.clientHeight + 1,
  )
}

/**
 * Smallest width from 40vw to 70vw at which every `[data-fit]` block is fully visible.
 * On a narrow screen the stylesheet takes the full width instead.
 */
export function useSheetWidth(measureKey: string) {
  const panelRef = useRef<HTMLElement>(null)
  const [vw, setVw] = useState(NARROW)

  useLayoutEffect(() => {
    const panel = panelRef.current
    if (!panel || measureKey === '' || window.matchMedia('(max-width: 720px)').matches) return

    let chosen = WIDE
    let low = NARROW
    let high = WIDE
    const previous = panel.style.width
    while (low <= high) {
      const mid = Math.ceil((low + high) / 2)
      panel.style.width = `${mid}vw`
      if (contentFits(panel)) {
        chosen = mid
        high = mid - 1
      } else {
        low = mid + 1
      }
    }
    panel.style.width = previous
    setVw((current) => (current === chosen ? current : chosen))
  }, [measureKey])

  return [panelRef, vw] as const
}
