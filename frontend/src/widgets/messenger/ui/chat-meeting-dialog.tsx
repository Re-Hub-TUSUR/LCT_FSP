import { useState } from 'react'
import type { FormEvent } from 'react'
import { useMutation } from '@tanstack/react-query'
import { conversationApi } from '@/entities/conversation'
import { getErrorMessage } from '@/shared/api'
import { toDateInput, toTimeInput } from '@/shared/lib'
import { Button, Modal, TextField } from '@/shared/ui'

type Props = {
  conversationId: string
  onClose: () => void
  onSent: () => void
}

export function ChatMeetingDialog({ conversationId, onClose, onSent }: Props) {
  const [location, setLocation] = useState('')
  const [date, setDate] = useState(() => toDateInput(new Date()))
  const [time, setTime] = useState(() => toTimeInput(new Date()))
  const [error, setError] = useState<string | null>(null)

  const send = useMutation({
    mutationFn: () => {
      const startsAt = new Date(`${date}T${time}:00`)
      const endsAt = new Date(startsAt.getTime() + 60 * 60_000)
      return conversationApi.sendMeeting(conversationId, {
        location: location.trim(),
        startsAt: startsAt.toISOString(),
        endsAt: endsAt.toISOString(),
        title: 'Собеседование',
      })
    },
    onSuccess: () => {
      onSent()
      onClose()
    },
    onError: (err) => setError(getErrorMessage(err)),
  })

  const submit = (event: FormEvent) => {
    event.preventDefault()
    setError(null)
    if (!location.trim()) {
      setError('Укажите ссылку на звонок')
      return
    }
    send.mutate()
  }

  return (
    <Modal title="Встреча" onClose={onClose}>
      <form className="chat-meeting" onSubmit={submit}>
        <TextField
          id="chat-meeting-link"
          label="Ссылка на звонок"
          value={location}
          onChange={(e) => setLocation(e.target.value)}
        />
        <TextField
          id="chat-meeting-date"
          label="Дата созвона"
          type="date"
          value={date}
          onChange={(e) => setDate(e.target.value)}
        />
        <TextField
          id="chat-meeting-time"
          label="Время созвона"
          type="time"
          value={time}
          onChange={(e) => setTime(e.target.value)}
        />
        {error ? <p className="chat-meeting__error">{error}</p> : null}
        <div className="chat-meeting__actions">
          <Button type="button" variant="ghost" onClick={onClose}>
            Отмена
          </Button>
          <Button type="submit" disabled={send.isPending}>
            Отправить
          </Button>
        </div>
      </form>
    </Modal>
  )
}
