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
  firstName?: string | null
  lastName?: string | null
  phone?: string | null
}

export type UserWrite = {
  firstName: string
  lastName: string
  phone: string | null
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

export const userApi = {
  /** Name and phone of the account owner (the recruiter, for employers). */
  updateMe: (payload: UserWrite) => http.patch<UserDto>('/users/me', payload),
}
