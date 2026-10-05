import { useRef, useState } from 'react'
import type { PointerEvent } from 'react'

const SWIPE_THRESHOLD_PX = 120
// Capturing the pointer immediately would retarget clicks on links/buttons inside the card.
const DRAG_START_PX = 6

type Handlers = {
  onSwipeLeft: () => void
  onSwipeRight: () => void
}

/** Minimal pointer-based horizontal swipe. Buttons and arrow keys remain the accessible path. */
export function useSwipe({ onSwipeLeft, onSwipeRight }: Handlers) {
  const startX = useRef<number | null>(null)
  const [offset, setOffset] = useState(0)

  const reset = () => {
    startX.current = null
    setOffset(0)
  }

  return {
    offset,
    bind: {
      onPointerDown: (e: PointerEvent<HTMLElement>) => {
        startX.current = e.clientX
      },
      onPointerMove: (e: PointerEvent<HTMLElement>) => {
        if (startX.current === null) return
        const dx = e.clientX - startX.current
        if (Math.abs(dx) < DRAG_START_PX) return
        if (!e.currentTarget.hasPointerCapture?.(e.pointerId)) {
          e.currentTarget.setPointerCapture?.(e.pointerId)
        }
        setOffset(dx)
      },
      onPointerUp: () => {
        if (offset <= -SWIPE_THRESHOLD_PX) onSwipeLeft()
        else if (offset >= SWIPE_THRESHOLD_PX) onSwipeRight()
        reset()
      },
      onPointerCancel: reset,
    },
  }
}
