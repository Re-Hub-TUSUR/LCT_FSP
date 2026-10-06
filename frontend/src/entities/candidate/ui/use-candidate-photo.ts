import { useQuery } from '@tanstack/react-query'
import { candidateApi, candidateKeys } from '../api/candidate-api'
import { cachePhotoUrl } from '../lib/photo-cache'

export function useCandidatePhoto(candidateId: string | null, enabled: boolean) {
  return useQuery({
    queryKey: [...candidateKeys.all, 'photo', candidateId],
    queryFn: async () => {
      const blob = await candidateApi.photo(candidateId ?? '')
      return cachePhotoUrl(candidateId ?? '', blob)
    },
    enabled: Boolean(candidateId) && enabled,
    staleTime: 300_000,
    retry: false,
  })
}
