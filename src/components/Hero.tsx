import { useCallback, useEffect, useRef, useState } from 'react'
import { LEGAL, MEDIA } from '../content.ts'
import MobileMenu from './MobileMenu.tsx'
import Navbar from './Navbar.tsx'
import SignupPanel from './SignupPanel.tsx'

export default function Hero() {
  const [menuOpen, setMenuOpen] = useState(false)
  const toggleRef = useRef<HTMLButtonElement>(null)
  const wasOpen = useRef(false)

  const closeMenu = useCallback(() => setMenuOpen(false), [])

  useEffect(() => {
    document.body.classList.toggle('menu-open', menuOpen)
    // Restore focus to the toggle only when the menu was actually closed by the user
    if (wasOpen.current && !menuOpen && toggleRef.current?.offsetParent) {
      toggleRef.current.focus()
    }
    wasOpen.current = menuOpen
    return () => document.body.classList.remove('menu-open')
  }, [menuOpen])

  useEffect(() => {
    if (!menuOpen) return
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') closeMenu()
    }
    const desktop = window.matchMedia('(min-width: 901px)')
    const onDesktop = (e: MediaQueryListEvent) => {
      if (e.matches) closeMenu()
    }
    document.addEventListener('keydown', onKey)
    desktop.addEventListener('change', onDesktop)
    return () => {
      document.removeEventListener('keydown', onKey)
      desktop.removeEventListener('change', onDesktop)
    }
  }, [menuOpen, closeMenu])

  return (
    <>
      <main className="hero">
        <div className="hero__media" aria-hidden="true">
          <video
            className="hero__video"
            src={MEDIA.video}
            poster={MEDIA.poster}
            autoPlay
            muted
            loop
            playsInline
            preload="auto"
          />
        </div>
        <div className="hero__scrim" aria-hidden="true" />

        <Navbar
          menuOpen={menuOpen}
          onToggle={() => setMenuOpen((v) => !v)}
          toggleRef={toggleRef}
        />

        <div className="hero__body">
          <SignupPanel />
        </div>

        <footer className="legal">
          <p>
            {LEGAL.before}
            <a href={LEGAL.privacy.href}>{LEGAL.privacy.label}</a>
            {LEGAL.between}
            <a href={LEGAL.terms.href}>{LEGAL.terms.label}</a>
            {LEGAL.after}
          </p>
        </footer>
      </main>

      <MobileMenu open={menuOpen} onClose={closeMenu} />
    </>
  )
}
