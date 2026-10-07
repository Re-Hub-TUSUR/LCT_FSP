import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'

export type MessageKind = 'text' | 'attachment' | 'meeting'

export type ConversationPeerDto = {
  id: string
  name: string
  subtitle: string | null
}

export type ConversationDto = {
  id: string
  peer: ConversationPeerDto
  lastMessageAt: string | null
  matched: boolean
}

export type AttachmentDto = {
  id: string
  filename: string
  mediaType: string
  sizeBytes: number
}

export type MeetingPreviewDto = {
  id: string
  title: string
  startsAt: string
  endsAt: string
  location: string | null
  status: 'pending' | 'confirmed' | 'declined'
}

export type MessageDto = {
  id: string
  conversationId: string
  senderId: string
  kind: MessageKind
  text: string | null
  attachment: AttachmentDto | null
  meeting: MeetingPreviewDto | null
  createdAt: string
}

export type MessagePageDto = {
  items: MessageDto[]
  hasMore: boolean
}

export type ChatMeetingPayload = {
  location: string
  startsAt: string
  endsAt?: string
  title?: string
  vacancyId?: string | null
}

export const conversationKeys = {
  all: ['conversations'] as const,
  list: () => [...conversationKeys.all, 'list'] as const,
  messages: (id: string) => [...conversationKeys.all, 'messages', id] as const,
}

export const conversationQueries = {
  list: () =>
    queryOptions({
      queryKey: conversationKeys.list(),
      queryFn: ({ signal }) => http.get<ConversationDto[]>('/conversations', { signal }),
    }),
  messages: (id: string) =>
    queryOptions({
      queryKey: conversationKeys.messages(id),
      queryFn: ({ signal }) =>
        http.get<MessagePageDto>(`/conversations/${id}/messages`, { signal }),
    }),
}

export const conversationApi = {
  sendText: (id: string, text: string) =>
    http.post<MessageDto>(`/conversations/${id}/messages`, { text }),
  sendAttachment: (id: string, file: File) => {
    const body = new FormData()
    body.append('file', file)
    return http.post<MessageDto>(`/conversations/${id}/attachments`, body)
  },
  sendMeeting: (id: string, payload: ChatMeetingPayload) =>
    http.post<MessageDto>(`/conversations/${id}/meetings`, payload),
  fetchAttachmentBlob: (id: string) => http.blob(`/conversations/attachments/${id}`),
}
