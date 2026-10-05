import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { CandidateDto } from '@/entities/candidate/@x/match'

/** One explained recommendation in the employer's candidate selection. */
export type MatchRecommendationDto = {
  candidate: CandidateDto
  /** 0..1, relevance to the employer's described need. */
  score: number
  /** Human-readable explanation why the candidate is in the selection (ТЗ: "объяснимость выдачи"). */
  reasons: string[]
}

export type MatchRecommendationsDto = {
  needId: string | null
  items: MatchRecommendationDto[]
}

export const matchKeys = {
  all: ['matching'] as const,
  recommendations: (needId?: string) =>
    [...matchKeys.all, 'recommendations', needId ?? null] as const,
}

export const matchQueries = {
  recommendations: (needId?: string) =>
    queryOptions({
      queryKey: matchKeys.recommendations(needId),
      queryFn: ({ signal }) =>
        http.get<MatchRecommendationsDto>('/matching/recommendations', {
          query: { needId },
          signal,
        }),
    }),
}
