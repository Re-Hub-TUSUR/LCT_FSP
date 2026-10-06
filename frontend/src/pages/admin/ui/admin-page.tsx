import { useQuery } from '@tanstack/react-query'
import { ROLE_LABELS, userQueries } from '@/entities/user'
import { formatDate } from '@/shared/lib'
import { Page, QueryState, Section } from '@/shared/ui'
import { AssessmentBank } from '@/widgets/assessment-bank'

/** TODO(admin): moderation of vacancies/companies (anti-fraud, out of MVP scope). */
export function AdminPage() {
  const users = useQuery(userQueries.adminList({ perPage: 50 }))

  return (
    <Page title="Администрирование">
      <Section title="Пользователи">
        <QueryState query={users} isEmpty={(page) => page.items.length === 0}>
          {(page) => (
            <table>
              <thead>
                <tr>
                  <th scope="col">Email</th>
                  <th scope="col">Роль</th>
                  <th scope="col">Email подтверждён</th>
                  <th scope="col">Создан</th>
                </tr>
              </thead>
              <tbody>
                {page.items.map((user) => (
                  <tr key={user.id}>
                    <td>{user.email}</td>
                    <td>{ROLE_LABELS[user.role]}</td>
                    <td>{user.isEmailVerified ? 'да' : 'нет'}</td>
                    <td>{formatDate(user.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </QueryState>
      </Section>
      <AssessmentBank scope="admin" />
    </Page>
  )
}
