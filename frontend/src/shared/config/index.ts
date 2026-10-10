export { isAdminHost } from './admin-host'
export { env } from './env'
export { ROUTES, paths } from './routes'
export type { MatchingProfileKind } from './routes'
export { STACK_SKILLS } from './skills'

export const BRAND = 'КАДРЫ'
/** The API takes salaries up to 100 million roubles a month (`MAX_SALARY`). */
export const MAX_SALARY = 100_000_000
export const MAX_SALARY_ERROR = 'Не больше 100 000 000 ₽'
