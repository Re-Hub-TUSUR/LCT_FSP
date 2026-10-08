import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Grade, SpecializationCode } from '../model/grade'

export type SpecializationDto = {
  code: SpecializationCode
  label: string
}

export type CategoryDictionaryDto = {
  specializations: SpecializationDto[]
  grades: { code: Grade; label: string }[]
  /** IT slang the search understands, lowercase; the first word is the usual one. */
  synonyms?: string[][]
}

export const categoryKeys = {
  all: ['categories'] as const,
  dictionary: () => [...categoryKeys.all, 'dictionary'] as const,
}

export const categoryQueries = {
  dictionary: () =>
    queryOptions({
      queryKey: categoryKeys.dictionary(),
      queryFn: ({ signal }) =>
        http.get<CategoryDictionaryDto>('/categories/dictionary', { signal }),
      staleTime: Infinity,
    }),
}
