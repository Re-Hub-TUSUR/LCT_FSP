import { useEffect, useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import {
  conversationApi,
  conversationKeys,
  conversationQueries,
  type MessageDto,
} from '@/entities/conversation'
import { calendarEventApi, calendarEventKeys } from '@/entities/calendar-event'
import { useSession } from '@/entities/session'
import { useNotificationStream } from '@/features/notification-stream'
import { getErrorMessage } from '@/shared/api'
import { isHttpUrl } from '@/shared/lib'
import { Avatar, Button, EmptyState, QueryState } from '@/shared/ui'
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

const time = new Intl.DateTimeFormat('ru-RU', { hour: '2-digit', minute: '2-digit' })
const day = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'short' })

/** Time for today's messages, the date for older ones. */
function formatShort(value: string) {
  const date = new Date(value)
  return date.toDateString() === new Date().toDateString() ? time.format(date) : day.format(date)
}

function formatSize(bytes: number) {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1024 * 1024) return `${Math.round(bytes / 1024)} КБ`
  return `${(bytes / 1024 / 1024).toFixed(1).replace('.', ',')} МБ`
}

/** The candidate answers a meeting, so the same status reads differently on each side. */
/** The API takes chat files up to 10 MB (`CHAT_ATTACHMENT_LIMIT`). */
const ATTACHMENT_LIMIT = 10 * 1024 * 1024
/** What the API accepts: photos, PDF and Word. A .pptx is a ZIP too, but it is refused. */
const ATTACHMENT_ACCEPT = 'image/jpeg,image/png,image/webp,image/gif,.pdf,.doc,.docx'

const MEETING_STATUS = {
  candidate: {
    pending: 'Ждёт вашего ответа',
    confirmed: 'Вы подтвердили',
    declined: 'Вы отклонили',
  },
  employer: {
    pending: 'Ждёт ответа кандидата',
    confirmed: 'Кандидат подтвердил',
    declined: 'Кандидат отклонил',
  },
} as const

type Side = keyof typeof MEETING_STATUS

/** The candidate's answer right in the chat: the same as in the calendar. */
function MeetingAnswer({
  meetingId,
  conversationId,
}: {
  meetingId: string
  conversationId: string
}) {
  const queryClient = useQueryClient()
  const respond = useMutation({
    mutationFn: (accept: boolean) => calendarEventApi.respond(meetingId, accept),
    onSuccess: () => {
      void queryClient.invalidateQueries({ queryKey: conversationKeys.messages(conversationId) })
      void queryClient.invalidateQueries({ queryKey: calendarEventKeys.all })
    },
  })
  return (
    <>
      <div className="chat-msg__meet-actions">
        <Button size="inline" disabled={respond.isPending} onClick={() => respond.mutate(true)}>
          Подтвердить
        </Button>
        <Button
          size="inline"
          variant="ghost"
          disabled={respond.isPending}
          onClick={() => respond.mutate(false)}
        >
          Отклонить
        </Button>
      </div>
      {respond.isError && (
        <p className="chat-msg__meet-error" role="alert">
          {getErrorMessage(respond.error)}
        </p>
      )}
    </>
  )
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

function MessageBubble({ message, own, side }: { message: MessageDto; own: boolean; side: Side }) {
  const stamp = (
    <time className="chat-msg__time" dateTime={message.createdAt}>
      {formatWhen(message.createdAt)}
    </time>
  )

  if (message.kind === 'meeting' && message.meeting) {
    const meet = message.meeting
    return (
      <div className={`chat-row${own ? ' is-own' : ''}`}>
        <article className={`chat-msg chat-msg--meeting is-${meet.status}`}>
          <p className="chat-msg__label">Встреча</p>
          <h4 className="chat-msg__meet-title">{meet.title}</h4>
          <p className="chat-msg__meet-when">
            {formatWhen(meet.startsAt)} — {formatWhen(meet.endsAt)}
          </p>
          {meet.location ? (
            // Only a web address becomes a link: `javascript:` and the like stay plain text.
            isHttpUrl(meet.location) ? (
              <a
                className="chat-msg__meet-link"
                href={meet.location}
                target="_blank"
                rel="noopener noreferrer"
              >
                {meet.location}
              </a>
            ) : (
              <p className="chat-msg__meet-place">{meet.location}</p>
            )
          ) : null}
          <p className="chat-msg__meet-status">
            {MEETING_STATUS[side][meet.status] ?? meet.status}
          </p>
          {side === 'candidate' && meet.status === 'pending' && (
            <MeetingAnswer meetingId={meet.id} conversationId={message.conversationId} />
          )}
        </article>
        {stamp}
      </div>
    )
  }

  if (message.kind === 'attachment' && message.attachment) {
    const att = message.attachment
    const image = att.mediaType.startsWith('image/')
    const extension = att.filename.includes('.') ? att.filename.split('.').pop() : 'файл'
    return (
      <div className={`chat-row${own ? ' is-own' : ''}`}>
        <article className="chat-msg chat-msg--file">
          {image ? (
            <ChatAttachmentImage id={att.id} alt={att.filename} />
          ) : (
            <button
              type="button"
              className="chat-msg__file"
              onClick={() => {
                // Saved under its own name: a document from a chat is not rendered on our origin.
                void conversationApi.fetchAttachmentBlob(att.id).then((blob) => {
                  const url = URL.createObjectURL(blob)
                  const link = document.createElement('a')
                  link.href = url
                  link.download = att.filename
                  link.click()
                  window.setTimeout(() => URL.revokeObjectURL(url), 60_000)
                })
              }}
            >
              <span className="chat-msg__ext" aria-hidden="true">
                {extension}
              </span>
              <span className="chat-msg__file-text">
                <span className="chat-msg__file-name">{att.filename}</span>
                <span className="chat-msg__file-size">{formatSize(att.sizeBytes)}</span>
              </span>
            </button>
          )}
        </article>
        {stamp}
      </div>
    )
  }

  return (
    <div className={`chat-row${own ? ' is-own' : ''}`}>
      <article className="chat-msg">
        <p>{message.text}</p>
      </article>
      {stamp}
    </div>
  )
}

export function Messenger({ selectedId, onSelect }: Props) {
  const { user } = useSession()
  const employer = user?.role === 'employer'
  const queryClient = useQueryClient()
  const [draft, setDraft] = useState('')
  const [meetingOpen, setMeetingOpen] = useState(false)
  const [sendError, setSendError] = useState<string | null>(null)
  // On a narrow screen the list and the chat take turns; this is which one is up.
  const [listUp, setListUp] = useState(true)
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

  const peer = listQuery.data?.find((item) => item.id === selectedId)?.peer

  const submit = () => {
    const text = draft.trim()
    if (!selectedId || !text || sendText.isPending) return
    setSendError(null)
    sendText.mutate(text)
  }

  return (
    <div className={listUp ? 'chat chat--list' : 'chat'}>
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
                      aria-current={selectedId === item.id ? 'true' : undefined}
                      onClick={() => {
                        onSelect(item.id)
                        setListUp(false)
                      }}
                    >
                      <Avatar name={item.peer.name} size="sm" />
                      <span className="chat__thread-text">
                        <span className="chat__thread-name">{item.peer.name}</span>
                        {item.peer.subtitle ? (
                          <span className="chat__thread-sub">{item.peer.subtitle}</span>
                        ) : null}
                      </span>
                      {item.lastMessageAt ? (
                        <time className="chat__thread-time" dateTime={item.lastMessageAt}>
                          {formatShort(item.lastMessageAt)}
                        </time>
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
            <header className="chat__head">
              <button type="button" className="chat__back" onClick={() => setListUp(true)}>
                ← Диалоги
              </button>
              {peer ? (
                <div className="chat__peer">
                  <h3 className="chat__peer-name">{peer.name}</h3>
                  {peer.subtitle ? <p className="chat__peer-sub">{peer.subtitle}</p> : null}
                </div>
              ) : null}
            </header>
            <div ref={streamRef} className="chat__stream">
              <QueryState query={messagesQuery} loadingLabel="Сообщения…">
                {(page) => (
                  <div className="chat__messages">
                    {page.items.map((message) => (
                      <MessageBubble
                        key={message.id}
                        message={message}
                        own={message.senderId === user?.id}
                        side={employer ? 'employer' : 'candidate'}
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
                accept={ATTACHMENT_ACCEPT}
                onChange={(event) => {
                  const file = event.target.files?.[0]
                  event.target.value = ''
                  if (!file || !selectedId) return
                  if (file.size > ATTACHMENT_LIMIT) {
                    setSendError('Файл больше 10 МБ: сожмите его или отправьте ссылкой.')
                    return
                  }
                  setSendError(null)
                  sendFile.mutate(file)
                }}
              />
              <input
                className="chat__input"
                aria-label="Сообщение"
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
              <button
                type="button"
                className="chat__send"
                aria-label="Отправить"
                disabled={!draft.trim() || sendText.isPending}
                onClick={submit}
              >
                →
              </button>
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
