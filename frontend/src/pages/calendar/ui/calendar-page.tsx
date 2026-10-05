import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CALENDAR_EVENT_KIND_LABELS, calendarEventQueries } from '@/entities/calendar-event'
import { formatDateTime } from '@/shared/lib'
import { Button, Page, QueryState, Tag } from '@/shared/ui'
import './calendar-page.css'

function monthRange(offset: number) {
  const now = new Date()
  const from = new Date(now.getFullYear(), now.getMonth() + offset, 1)
  const to = new Date(now.getFullYear(), now.getMonth() + offset + 1, 1)
  return { from: from.toISOString(), to: to.toISOString(), label: from }
}

const monthLabel = new Intl.DateTimeFormat('ru-RU', { month: 'long', year: 'numeric' })

/** Interviews, assessment slots and task deadlines of the signed-in user. */
export function CalendarPage() {
  const [offset, setOffset] = useState(0)
  const { from, to, label } = monthRange(offset)
  const events = useQuery(calendarEventQueries.range({ from, to }))

  // TODO(calendar): month grid view; for MVP an agenda list is enough.
  return (
    <Page
      title="Календарь"
      lead={monthLabel.format(label)}
      actions={
        <>
          <Button variant="ghost" size="inline" onClick={() => setOffset((v) => v - 1)}>
            Назад
          </Button>
          <Button variant="ghost" size="inline" onClick={() => setOffset((v) => v + 1)}>
            Вперёд
          </Button>
        </>
      }
    >
      <QueryState query={events} isEmpty={(list) => list.length === 0} emptyTitle="Событий нет">
        {(list) => (
          <ol className="agenda">
            {list.map((event) => (
              <li key={event.id} className="agenda__item">
                <time dateTime={event.startsAt}>{formatDateTime(event.startsAt)}</time>
                <span>{event.title}</span>
                <Tag>{CALENDAR_EVENT_KIND_LABELS[event.kind]}</Tag>
              </li>
            ))}
          </ol>
        )}
      </QueryState>
    </Page>
  )
}
