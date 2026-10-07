import { useEffect, useRef, useState } from 'react'

/** True when the element is clipped by its box. `measureKey` reruns the check after the content changes. */
export function useOverflows(measureKey: string) {
  const ref = useRef<HTMLDivElement>(null)
  const [overflows, setOverflows] = useState(false)

  useEffect(() => {
    const element = ref.current
    if (!element || measureKey === '') return
    const measure = () => setOverflows(element.scrollHeight > element.clientHeight + 1)
    measure()
    if (typeof ResizeObserver === 'undefined') return
    const observer = new ResizeObserver(measure)
    observer.observe(element)
    return () => observer.disconnect()
  }, [measureKey])

  return [ref, overflows] as const
}
