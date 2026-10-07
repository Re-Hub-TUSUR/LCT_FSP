import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  conversationApi,
  conversationKeys,
  conversationQueries,
  type MessageDto,
} from '@/entities/conversation'
import { useSession } from '@/entities/session'
import { useNotificationStream } from '@/features/notification-stream'
import { getErrorMessage } from '@/shared/api'
import { Button, EmptyState, QueryState } from '@/shared/ui'
import { ChatMeetingDialog } from './chat-meeting-dialog'
import './messenger.css'

type Props = {
  selectedId: string | null
  onSelect: (id: string) => void
}

function formatWhen(value: string) {
  return new Intl.DateTimeFormat('ru-RU', {
    day: 'numeric',
    month: 'short',
    hour: '2-digit',
    minute: '2-digit',
  }).format(new Date(value))
}

function ChatAttachmentImage({ id, alt }: { id: string; alt: string }) {
  const [src, setSrc] = useState<string | null>(null)
  useEffect(() => {
    let alive = true
    let objectUrl: string | null = null
    void conversationApi.fetchAttachmentBlob(id).then((blob) => {
      if (!alive) return
      objectUrl = URL.createObjectURL(blob)
      setSrc(objectUrl)
    })
    return () => {
      alive = false
      if (objectUrl) URL.revokeObjectURL(objectUrl)
    }
  }, [id])
  if (!src) return <span className="chat-msg__file">{alt}</span>
  return <img className="chat-msg__image" src={src} alt={alt} />
}

function MessageBubble({ message, own }: { message: MessageDto; own: boolean }) {
  if (message.kind === 'meeting' && message.meeting) {
    const meet = message.meeting
    return (
      <article className={`chat-msg chat-msg--meeting${own ? ' is-own' : ''}`}>
        <p className="chat-msg__label">Встреча</p>
        <h4 className="chat-msg__meet-title">{meet.title}</h4>
        <p className="chat-msg__meet-when">
          {formatWhen(meet.startsAt)} — {formatWhen(meet.endsAt)}
        </p>
        {meet.location ? (
          <a className="chat-msg__meet-link" href={meet.location} target="_blank" rel="noreferrer">
            {meet.location}
          </a>
        ) : null}
        <p className="chat-msg__meet-status">{meet.status}</p>
      </article>
    )
  }

  if (message.kind === 'attachment' && message.attachment) {
    const att = message.attachment
    const image = att.mediaType.startsWith('image/')
    return (
      <article className={`chat-msg chat-msg--file${own ? ' is-own' : ''}`}>
        {image ? (
          <ChatAttachmentImage id={att.id} alt={att.filename} />
        ) : (
          <button
            type="button"
            className="chat-msg__file"
            onClick={() => {
              void conversationApi.fetchAttachmentBlob(att.id).then((blob) => {
                const url = URL.createObjectURL(blob)
                window.open(url, '_blank', 'noopener,noreferrer')
                window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
              })
            }}
          >
            {att.filename}
          </button>
        )}
      </article>
    )
  }

  return (
    <article className={`chat-msg${own ? ' is-own' : ''}`}>
      <p>{message.text}</p>
    </article>
  )
}

export function Messenger({ selectedId, onSelect }: Props) {
  const { user } = useSession()
  const employer = user?.role === 'employer'
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState('')
  const [meetingOpen, setMeetingOpen] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  const fileRef = useRef<HTMLInputElement>(null)
  const streamRef = useRef<HTMLDivElement>(null)

  const listQuery = useQuery(conversationQueries.list())
  const messagesQuery = useQuery({
    ...conversationQueries.messages(selectedId ?? ''),
    enabled: Boolean(selectedId),
    refetchInterval: 8000,
  })

  useNotificationStream({
    onMessage: (event) => {
      if (event.conversationId === selectedId) {
        void queryClient.invalidateQueries({
          queryKey: conversationKeys.messages(event.conversationId),
        })
      }
    },
  })

  useEffect(() => {
    const first = listQuery.data?.[0]
    if (!selectedId && first) onSelect(first.id)
  }, [listQuery.data, onSelect, selectedId])

  useEffect(() => {
    const node = streamRef.current
    const items = messagesQuery.data?.items
    if (!node || !selectedId || !items?.length) return
    node.scrollTop = node.scrollHeight
  }, [messagesQuery.data?.items, selectedId])

  const sendText = useMutation({
    mutationFn: (text: string) => conversationApi.sendText(selectedId!, text),
    onSuccess: () => {
      setDraft('')
      void queryClient.invalidateQueries({ queryKey: conversationKeys.messages(selectedId!) })
      void queryClient.invalidateQueries({ queryKey: conversationKeys.list() })
    },
    onError: (err) => setSendError(getErrorMessage(err)),
  })

  const sendFile = useMutation({
    mutationFn: (file: File) => conversationApi.sendAttachment(selectedId!, file),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: conversationKeys.messages(selectedId!) })
      void queryClient.invalidateQueries({ queryKey: conversationKeys.list() })
    },
    onError: (err) => setSendError(getErrorMessage(err)),
  })

  const submit = () => {
    const text = draft.trim()
    if (!selectedId || !text || sendText.isPending) return
    setSendError(null)
    sendText.mutate(text)
  }

  return (
    <div className="chat">
      <aside className="chat__sidebar" aria-label="Диалоги">
        <QueryState query={listQuery} loadingLabel="Диалоги…">
          {(items) =>
            items.length ? (
              <ul className="chat__threads">
                {items.map((item) => (
                  <li key={item.id}>
                    <button
                      type="button"
                      className={`chat__thread${selectedId === item.id ? ' is-active' : ''}`}
                      onClick={() => onSelect(item.id)}
                    >
                      <span className="chat__thread-name">{item.peer.name}</span>
                      {item.peer.subtitle ? (
                        <span className="chat__thread-sub">{item.peer.subtitle}</span>
                      ) : null}
                    </button>
                  </li>
                ))}
              </ul>
            ) : (
              <EmptyState title="Сообщений пока нет">
                Чат откроется после взаимной симпатии — ответьте на входящий лайк или дождитесь
                ответа.
              </EmptyState>
            )
          }
        </QueryState>
      </aside>

      <section className="chat__pane">
        {!selectedId ? (
          <EmptyState title="Выберите диалог">
            Слева — ваши совпадения с взаимным интересом.
          </EmptyState>
        ) : (
          <>
            <div ref={streamRef} className="chat__stream">
              <QueryState query={messagesQuery} loadingLabel="Сообщения…">
                {(page) => (
                  <div className="chat__messages">
                    {page.items.map((message) => (
                      <MessageBubble
                        key={message.id}
                        message={message}
                        own={message.senderId === user?.id}
                      />
                    ))}
                  </div>
                )}
              </QueryState>
            </div>

            <div className="chat__composer">
              <button
                type="button"
                className="chat__attach"
                aria-label="Прикрепить файл"
                onClick={() => fileRef.current?.click()}
              >
                +
              </button>
              <input
                ref={fileRef}
                type="file"
                hidden
                accept="image/*,.pdf,.doc,.docx"
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  event.target.value = ''
                  if (!file || !selectedId) return
                  setSendError(null)
                  sendFile.mutate(file)
                }}
              />
              <input
                className="chat__input"
                placeholder="Сообщение"
                value={draft}
                onChange={(e) => setDraft(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault()
                    submit()
                  }
                }}
              />
              {employer ? (
                <button type="button" className="chat__meet" onClick={() => setMeetingOpen(true)}>
                  Встреча
                </button>
              ) : null}
              <Button size="inline" disabled={!draft.trim() || sendText.isPending} onClick={submit}>
                →
              </Button>
            </div>
            {sendError ? <p className="chat__error">{sendError}</p> : null}
          </>
        )}
      </section>

      {meetingOpen && selectedId ? (
        <ChatMeetingDialog
          conversationId={selectedId}
          onClose={() => setMeetingOpen(false)}
          onSent={() => {
            void queryClient.invalidateQueries({ queryKey: conversationKeys.messages(selectedId) })
            void queryClient.invalidateQueries({ queryKey: conversationKeys.list() })
          }}
        />
      ) : null}
    </div>
  )
}
