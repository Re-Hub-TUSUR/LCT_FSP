import { useCallback, useEffect, useRef, useState } from 'react'

const DESKTOP_QUERY = '(min-width: 901px)'

export function useMobileMenu() {
  const [open, setOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)
  const wasOpen = useRef(false)

  const close = useCallback(() => setOpen(false), [])
  const toggle = useCallback(() => setOpen((v) => !v), [])

  useEffect(() => {
    document.body.classList.toggle('menu-open', open)
    // Restore focus to the toggle only when the menu was actually closed by the user
    if (wasOpen.current && !open && toggleRef.current?.offsetParent) {
      toggleRef.current.focus()
    }
    wasOpen.current = open
    return () => document.body.classList.remove('menu-open')
  }, [open])

  useEffect(() => {
    if (!open) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') close()
    }
    const desktop = window.matchMedia(DESKTOP_QUERY)
    const onDesktop = (e: MediaQueryListEvent) => {
      if (e.matches) close()
    }
    document.addEventListener('keydown', onKey)
    desktop.addEventListener('change', onDesktop)
    return () => {
      document.removeEventListener('keydown', onKey)
      desktop.removeEventListener('change', onDesktop)
    }
  }, [open, close])

  return { open, toggle, close, toggleRef }
}
