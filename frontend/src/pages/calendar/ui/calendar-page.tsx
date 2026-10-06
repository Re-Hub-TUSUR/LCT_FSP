import { useSession } from '@/entities/session'
import { Page } from '@/shared/ui'
import { MeetingCalendar } from '@/widgets/meeting-calendar'

/** Interviews of the signed-in user: the company schedules them, the candidate answers. */
export function CalendarPage() {
  const { user } = useSession()

  return (
    <Page
      title="Календарь"
      lead={user?.role === 'employer' ? 'Встречи с кандидатами' : 'Встречи с компаниями'}
    >
      <MeetingCalendar />
    </Page>
  )
}
