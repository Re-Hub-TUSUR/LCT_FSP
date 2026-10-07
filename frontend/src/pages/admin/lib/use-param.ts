import { useCallback } from 'react'
import { useSearchParams } from 'react-router'

/** One search parameter of the admin page as state; the other parameters are kept. */
export function useParam(name: string): [string | null, (value: string | null) => void] {
  const [params, setParams] = useSearchParams()
  const set = useCallback(
    (value: string | null) =>
      setParams((current) => {
        const next = new URLSearchParams(current)
        if (value === null || value === '') next.delete(name)
        else next.set(name, value)
        return next
      }),
    [name, setParams],
  )
  return [params.get(name), set]
}
