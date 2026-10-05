/** Common DTOs shared by several backend resources. */

export type Paginated<T> = {
  items: T[]
  total: number
  limit: number
  offset: number
}

export type PaginationParams = {
  limit?: number
  offset?: number
}

/** Salary is always a mandatory "from–to" range in roubles (see ТЗ, section 2.2). */
export type SalaryRangeDto = {
  from: number
  to: number
}
