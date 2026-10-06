import { useMobileMenu } from '../model/use-mobile-menu'
import type { NavItem } from '../model/types'
import { MobileMenu } from './mobile-menu'
import { Navbar } from './navbar'
import './site-header.css'

type Props = {
  links: readonly NavItem[]
  cta?: NavItem
  /** Logo target. Defaults to the landing page. */
  home?: string
  overlay?: boolean
}

export function SiteHeader({ links, cta, home, overlay = false }: Props) {
  const menu = useMobileMenu()

  return (
    <>
      <Navbar
        links={links}
        cta={cta}
        home={home}
        menuOpen={menu.open}
        onToggle={menu.toggle}
        toggleRef={menu.toggleRef}
        overlay={overlay}
      />
      <MobileMenu links={links} cta={cta} open={menu.open} onClose={menu.close} />
    </>
  )
}
