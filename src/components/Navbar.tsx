import type { RefObject } from 'react'
import { BRAND, MENU, NAV_CTA, NAV_LINKS } from '../content.ts'

type Props = {
  menuOpen: boolean
  onToggle: () => void
  toggleRef: RefObject<HTMLButtonElement | null>
}

export default function Navbar({ menuOpen, onToggle, toggleRef }: Props) {
  return (
    <header className="nav">
      <a className="nav__logo" href="#">
        {BRAND}
      </a>

      <div className="nav__right">
        <nav className="nav__links" aria-label="Основная навигация">
          {NAV_LINKS.map((link) => (
            <a key={link.href} className="nav__link" href={link.href}>
              {link.label}
            </a>
          ))}
        </nav>

        <a className="nav__cta" href={NAV_CTA.href}>
          {NAV_CTA.label}
        </a>

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
