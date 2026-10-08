import { useSession } from '@/entities/session'
import { HackerRain, HackerText, Page } from '@/shared/ui'
import { MeetingCalendar } from '@/widgets/meeting-calendar'
import './calendar-page.css'

/** Interviews of the signed-in user: the company schedules them, the candidate answers. */
export function CalendarPage() {
  const { user } = useSession()

  return (
    <Page
      className="page--calendar"
      title={<HackerText text="Календарь" />}
      lead={user?.role === 'employer' ? 'Встречи с кандидатами' : 'Встречи с компаниями'}
      backdrop={<HackerRain />}
    >
      <MeetingCalendar />
    </Page>
  )
}
