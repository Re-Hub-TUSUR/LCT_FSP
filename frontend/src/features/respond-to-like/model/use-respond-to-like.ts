import { useMutation, useQueryClient } from '@tanstack/react-query'
import { candidateKeys } from '@/entities/candidate'
import { conversationKeys, conversationQueries } from '@/entities/conversation'
import { responseApi, responseKeys } from '@/entities/response'
import { vacancyKeys } from '@/entities/vacancy'

/** Whose like is answered: a company's (by a candidate) or a candidate's (by a recruiter). */
export type LikeAnswer = { companyId?: string; candidateId?: string; vacancyId?: string }

/**
 * Likes back. The interest is mutual from then on, so the chat with the other side exists:
 * `onAnswered` gets its id (null when it could not be found) to open it.
 */
export function useRespondToLike(onAnswered: (chatId: string | null) => void) {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: async ({ companyId, candidateId, vacancyId }: LikeAnswer) => {
      if (companyId) await responseApi.respondCompany(companyId, vacancyId)
      else if (candidateId) await responseApi.respondCandidate(candidateId, vacancyId)
      const peerId = companyId ?? candidateId
      await queryClient.invalidateQueries({ queryKey: conversationKeys.list() })
      const chats = await queryClient.fetchQuery(conversationQueries.list()).catch(() => [])
      return chats.find((chat) => chat.peer.id === peerId)?.id ?? null
    },
    onSuccess: (chatId) => {
      void queryClient.invalidateQueries({ queryKey: responseKeys.inbound() })
      void queryClient.invalidateQueries({ queryKey: vacancyKeys.all })
      void queryClient.invalidateQueries({ queryKey: candidateKeys.all })
      onAnswered(chatId)
    },
  })
}
