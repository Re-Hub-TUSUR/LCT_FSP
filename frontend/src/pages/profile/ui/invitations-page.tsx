import { Link } from 'react-router'
import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { EmptyState, Page } from '@/shared/ui'
import { InvitationsBoard } from '@/widgets/invitations-inbox'

export function InvitationsPage() {
  const { user } = useSession()
  if (user?.role === 'employer') {
    return (
      <Page
        className="page--inset"
        title="Приглашения"
        lead="Кому вы отправили предложение и что ответили. Контакты откроются после согласия кандидата."
      >
        <InvitationsBoard
          direction="outgoing"
          empty={
            <EmptyState title="Вы ещё никого не пригласили">
              <Link className="cabinet-link" to={ROUTES.feed}>
                Открыть банк кандидатов
              </Link>
            </EmptyState>
          }
        />
      </Page>
    )
  }
  return (
    <Page
      className="page--inset"
      title="Приглашения"
      lead="Работодатели находят вас по категории и присылают предложение с зарплатой. Контакты они увидят, только когда вы примете приглашение."
    >
      <InvitationsBoard
        direction="incoming"
        empty={
          <EmptyState title="Приглашений пока нет">
            <Link className="cabinet-link" to={ROUTES.feed}>
              Смотреть вакансии
            </Link>
          </EmptyState>
        }
      />
    </Page>
  )
}
