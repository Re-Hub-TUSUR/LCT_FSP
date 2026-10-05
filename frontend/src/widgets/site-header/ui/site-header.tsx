import { useMobileMenu } from '../model/use-mobile-menu'
import type { NavItem } from '../model/types'
import { MobileMenu } from './mobile-menu'
import { Navbar } from './navbar'
import './site-header.css'

type Props = {
  links: readonly NavItem[]
  cta: NavItem
}

export function SiteHeader({ links, cta }: Props) {
  const menu = useMobileMenu()

  return (
    <>
      <Navbar
        links={links}
        cta={cta}
        menuOpen={menu.open}
        onToggle={menu.toggle}
        toggleRef={menu.toggleRef}
      />
      <MobileMenu links={links} cta={cta} open={menu.open} onClose={menu.close} />
    </>
  )
}
