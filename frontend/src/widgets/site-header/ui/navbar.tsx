import type { RefObject } from 'react'
import { Link } from 'react-router'
import { BRAND, ROUTES } from '@/shared/config'
import { MENU } from '../model/types'
import type { NavItem } from '../model/types'

type Props = {
  links: readonly NavItem[]
  cta: NavItem
  menuOpen: boolean
  onToggle: () => void
  toggleRef: RefObject<HTMLButtonElement | null>
  /** Transparent bar over the landing video. App pages use the sticky glass bar. */
  overlay?: boolean
}

export function Navbar({ links, cta, menuOpen, onToggle, toggleRef, overlay = false }: Props) {
  return (
    <header className={overlay ? 'nav nav--overlay' : 'nav'}>
      <Link className="nav__logo" to={ROUTES.landing}>
        {BRAND}
      </Link>

      <div className="nav__right">
        <nav className="nav__links" aria-label="Основная навигация">
          {links.map((link) => (
            <Link key={link.to} className="nav__link" to={link.to}>
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
