import { useEffect, useState } from 'react'
import type { MouseEvent, RefObject } from 'react'
import { Link, NavLink } from 'react-router'
import { BRAND, ROUTES } from '@/shared/config'
import { scrollToId } from '../lib/scroll-to-hash'
import { MENU } from '../model/types'
import type { NavItem } from '../model/types'
import { LogoMark } from './logo-mark'

type Props = {
  links: readonly NavItem[]
  cta?: NavItem
  home?: string
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

export function Navbar({
  links,
  cta,
  home = ROUTES.landing,
  menuOpen,
  onToggle,
  toggleRef,
  overlay = false,
}: Props) {
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
      <Link className="nav__logo" to={home}>
        <LogoMark />
        {BRAND}
      </Link>

      <div className="nav__right">
        <nav className="nav__links" aria-label="Основная навигация">
          {links.map((link) => (
            <NavLink
              key={link.to}
              className={({ isActive }) =>
                !link.to.startsWith('#') && isActive ? 'nav__link is-active' : 'nav__link'
              }
              to={link.to}
              end
              onClick={(event) => onHashClick(event, link.to)}
            >
              {link.label}
            </NavLink>
          ))}
        </nav>

        {cta && (
          <Link className="nav__cta" to={cta.to}>
            {cta.label}
          </Link>
        )}

        {(links.length > 0 || cta) && (
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
        )}
      </div>
    </header>
  )
}
