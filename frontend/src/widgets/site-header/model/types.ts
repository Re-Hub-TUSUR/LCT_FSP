export type NavItem = {
  label: string
  /** Route path (`/vacancies`) or in-page anchor (`#about`). */
  to: string
}

export const MENU = {
  id: 'mobileMenu',
  label: 'Меню сайта',
  open: 'Открыть меню',
  close: 'Закрыть меню',
}
