import { useEffect, useState } from 'react'
import type { MouseEvent, RefObject } from 'react'
import { Link } from 'react-router'
import { BRAND, ROUTES } from '@/shared/config'
import { scrollToId } from '../lib/scroll-to-hash'
import { MENU } from '../model/types'
import type { NavItem } from '../model/types'
import { LogoMark } from './logo-mark'

type Props = {
  links: readonly NavItem[]
  cta: NavItem
  menuOpen: boolean
  onToggle: () => void
  toggleRef: RefObject<HTMLButtonElement | null>
  /** Transparent bar over the landing video. App pages use the sticky glass bar. */
  overlay?: boolean
}

function onHashClick(event: MouseEvent<HTMLAnchorElement>, to: string) {
  if (!to.startsWith('#')) return
  event.preventDefault()
  scrollToId(to)
}

export function Navbar({ links, cta, menuOpen, onToggle, toggleRef, overlay = false }: Props) {
  const [scrolled, setScrolled] = useState(false)

  useEffect(() => {
    if (!overlay) return
    const onScroll = () => setScrolled(window.scrollY > 24)
    onScroll()
    window.addEventListener('scroll', onScroll, { passive: true })
    return () => window.removeEventListener('scroll', onScroll)
  }, [overlay])

  const bar = overlay ? `nav nav--overlay${scrolled ? ' is-scrolled' : ''}` : 'nav'

  return (
    <header className={bar}>
      <Link className="nav__logo" to={ROUTES.landing}>
        <LogoMark />
        {BRAND}
      </Link>

      <div className="nav__right">
        <nav className="nav__links" aria-label="Основная навигация">
          {links.map((link) => (
            <Link
              key={link.to}
              className="nav__link"
              to={link.to}
              onClick={(event) => onHashClick(event, link.to)}
            >
              {link.label}
            </Link>
          ))}
        </nav>

        <Link className="nav__cta" to={cta.to}>
          {cta.label}
        </Link>

        <button
          ref={toggleRef}
          type="button"
          className={`nav__toggle${menuOpen ? ' is-active' : ''}`}
          aria-expanded={menuOpen}
          aria-controls={MENU.id}
          aria-label={menuOpen ? MENU.close : MENU.open}
          onClick={onToggle}
        >
          <span />
          <span />
          <span />
        </button>
      </div>
    </header>
  )
}
