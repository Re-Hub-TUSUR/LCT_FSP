import { useEffect, useRef } from 'react'
import { useQueryClient } from '@tanstack/react-query'
import { companyKeys } from '@/entities/company'
import { conversationKeys } from '@/entities/conversation'
import { responseKeys } from '@/entities/response'
import { useSession } from '@/entities/session'
import { env } from '@/shared/config'

export type CompanyLikedEvent = {
  type: 'company_liked'
  companyId: string
  companyName: string
}

export type MessageEvent = {
  type: 'message'
  conversationId: string
  message: unknown
}

/** An admin decided on the company's Минцифры extract. */
export type CompanyVerificationEvent = {
  type: 'company_verification'
  status: 'approved' | 'rejected'
  reason: string | null
}

export type NotificationEvent = CompanyLikedEvent | MessageEvent | CompanyVerificationEvent

type Handlers = {
  onCompanyLiked?: (event: CompanyLikedEvent) => void
  onMessage?: (event: MessageEvent) => void
  onCompanyVerification?: (event: CompanyVerificationEvent) => void
}

/** SSE for employer likes, new chat messages and the IT accreditation decision. */
export function useNotificationStream(handlers: Handlers) {
  const { session } = useSession()
  const accessToken = session?.accessToken
  const queryClient = useQueryClient()
  const handlersRef = useRef(handlers)

  useEffect(() => {
    handlersRef.current = handlers
  })

  useEffect(() => {
    if (!accessToken) return

    const url = `${env.apiUrl}/notifications/stream`
    const controller = new AbortController()
    void (async () => {
      try {
        const response = await fetch(url, {
          headers: {
            Accept: 'text/event-stream',
            Authorization: `Bearer ${accessToken}`,
            'X-Kadry-Request': '1',
          },
          credentials: 'include',
          signal: controller.signal,
        })
        if (!response.ok || !response.body) return
        const reader = response.body.getReader()
        const decoder = new TextDecoder()
        let buffer = ''
        while (true) {
          const { done, value } = await reader.read()
          if (done) break
          buffer += decoder.decode(value, { stream: true })
          const chunks = buffer.split('\n\n')
          buffer = chunks.pop() ?? ''
          for (const chunk of chunks) {
            const line = chunk.split('\n').find((row) => row.startsWith('data: '))
            if (!line) continue
            const payload = JSON.parse(line.slice(6)) as NotificationEvent
            if (payload.type === 'company_liked') {
              handlersRef.current.onCompanyLiked?.(payload)
              void queryClient.invalidateQueries({ queryKey: responseKeys.inbound() })
            }
            if (payload.type === 'message') {
              handlersRef.current.onMessage?.(payload)
              void queryClient.invalidateQueries({ queryKey: conversationKeys.all })
            }
            if (payload.type === 'company_verification') {
              handlersRef.current.onCompanyVerification?.(payload)
              // The extract status and `itAccredited` of the company profile.
              void queryClient.invalidateQueries({ queryKey: companyKeys.all })
            }
          }
        }
      } catch {
        /* reconnect on next mount / token change */
      }
    })()

    return () => controller.abort()
  }, [accessToken, queryClient])
}
