import type { CSSProperties, MouseEvent } from 'react'
import { Link, NavLink } from 'react-router'
import { scrollToId } from '../lib/scroll-to-hash'
import { MENU } from '../model/types'
import type { NavItem } from '../model/types'

type Props = {
  links: readonly NavItem[]
  cta: NavItem
  open: boolean
  onClose: () => void
}

const stagger = (i: number) => ({ '--i': i }) as CSSProperties

export function MobileMenu({ links, cta, open, onClose }: Props) {
  const onBackdrop = (e: MouseEvent<HTMLElement>) => {
    if (e.target === e.currentTarget) onClose()
  }

  // Backdrop click is a pointer convenience; keyboard users close the menu with Escape.
  return (
    // oxlint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions
    <div
      id={MENU.id}
      className={`menu${open ? ' is-open' : ''}`}
      role="dialog"
      aria-modal="true"
      aria-label={MENU.label}
      aria-hidden={!open}
      inert={!open}
      onClick={onBackdrop}
    >
      {/* oxlint-disable-next-line jsx-a11y/click-events-have-key-events, jsx-a11y/no-noninteractive-element-interactions */}
      <nav className="menu__list" onClick={onBackdrop}>
        {links.map((link, i) => (
          <NavLink
            key={link.to}
            className={({ isActive }) =>
              !link.to.startsWith('#') && isActive ? 'menu__link is-active' : 'menu__link'
            }
            to={link.to}
            end
            style={stagger(i)}
            onClick={(event) => {
              onClose()
              if (!link.to.startsWith('#')) return
              event.preventDefault()
              requestAnimationFrame(() => scrollToId(link.to))
            }}
          >
            {link.label}
          </NavLink>
        ))}
        <Link className="menu__cta" to={cta.to} style={stagger(links.length)} onClick={onClose}>
          {cta.label}
        </Link>
      </nav>
    </div>
  )
}
