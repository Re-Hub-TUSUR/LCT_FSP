import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated, PaginationParams, SalaryRangeDto } from '@/shared/api'
import type { CategoryDto, Grade, SpecializationCode } from '@/entities/category/@x/vacancy'
import type { WorkFormat } from '../model/work-format'

export type VacancyDto = {
  id: string
  title: string
  company: { id: string; name: string }
  category: CategoryDto
  stack: string[]
  salary: SalaryRangeDto
  workFormat: WorkFormat
  publishedAt: string
}

export type VacancyListParams = PaginationParams & {
  search?: string
  specialization?: SpecializationCode
  grade?: Grade
  workFormat?: WorkFormat
}

export const vacancyKeys = {
  all: ['vacancies'] as const,
  list: (params: VacancyListParams) => [...vacancyKeys.all, 'list', params] as const,
  detail: (id: string) => [...vacancyKeys.all, 'detail', id] as const,
}

export const vacancyQueries = {
  list: (params: VacancyListParams = {}) =>
    queryOptions({
      queryKey: vacancyKeys.list(params),
      queryFn: ({ signal }) =>
        http.get<Paginated<VacancyDto>>('/vacancies', { query: params, signal }),
    }),
  detail: (id: string) =>
    queryOptions({
      queryKey: vacancyKeys.detail(id),
      queryFn: ({ signal }) => http.get<VacancyDto>(`/vacancies/${id}`, { signal }),
      enabled: Boolean(id),
    }),
}
