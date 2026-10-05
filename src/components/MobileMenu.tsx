import type { CSSProperties, MouseEvent } from 'react'
import { MENU, NAV_CTA, NAV_LINKS } from '../content.ts'

type Props = {
  open: boolean
  onClose: () => void
}

const stagger = (i: number) => ({ '--i': i }) as CSSProperties

export default function MobileMenu({ open, onClose }: Props) {
  const onBackdrop = (e: MouseEvent<HTMLDivElement>) => {
    if (e.target === e.currentTarget) onClose()
  }

  return (
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
      <nav className="menu__list" onClick={onBackdrop}>
        {NAV_LINKS.map((link, i) => (
          <a
            key={link.href}
            className="menu__link"
            href={link.href}
            style={stagger(i)}
            onClick={onClose}
          >
            {link.label}
          </a>
        ))}
        <a
          className="menu__cta"
          href={NAV_CTA.href}
          style={stagger(NAV_LINKS.length)}
          onClick={onClose}
        >
          {NAV_CTA.label}
        </a>
      </nav>
    </div>
  )
}
