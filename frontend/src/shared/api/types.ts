/** Common DTOs shared by several backend resources. */

/** One page of a list. `page` starts at 1; `pages` is 0 when nothing matched. */
export type Paginated<T> = {
  items: T[]
  total: number
  page: number
  perPage: number
  pages: number
}

export type PaginationParams = {
  page?: number
  perPage?: number
}

/** Salary is always a mandatory "from–to" range in roubles (see ТЗ, section 2.2). */
export type SalaryRangeDto = {
  from: number
  to: number
}
