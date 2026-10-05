import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams } from '@/shared/api'
import type { UserRole } from '../model/role'

export type UserDto = {
  id: string
  email: string
  role: UserRole
  isEmailVerified: boolean
  createdAt: string
}

export const userKeys = {
  all: ['users'] as const,
  adminList: (params: PaginationParams) => [...userKeys.all, 'admin-list', params] as const,
}

export const userQueries = {
  /** Admin-only listing of all accounts. */
  adminList: (params: PaginationParams = {}) =>
    queryOptions({
      queryKey: userKeys.adminList(params),
      queryFn: ({ signal }) =>
        http.get<Paginated<UserDto>>('/admin/users', { query: params, signal }),
    }),
}
