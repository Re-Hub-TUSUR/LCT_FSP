import { useState } from 'react'
import { keepPreviousData, useQuery } from '@tanstack/react-query'
import { ROLE_LABELS } from '@/entities/user'
import { formatDate } from '@/shared/lib'
import { EmptyState, ErrorState, Loader } from '@/shared/ui'
import { adminQueries } from '../../api/admin-api'
import { errorText } from '../../lib/format'
import { ExportButton } from '../common/export-button'
import { Pager } from '../common/pager'

export function UsersSection() {
  const [page, setPage] = useState(1)
  const users = useQuery({ ...adminQueries.users(page), placeholderData: keepPreviousData })

  return (
    <section className="admin-section">
      <header className="admin-section__head">
        <h1 className="admin-section__title">Пользователи</h1>
        <div className="admin-section__actions">
          <ExportButton path="/admin/users/export.csv" filename="users.csv" />
        </div>
      </header>
      {users.isPending ? (
        <Loader />
      ) : users.isError ? (
        <ErrorState message={errorText(users.error)} onRetry={() => void users.refetch()} />
      ) : users.data.items.length === 0 ? (
        <EmptyState title="Пользователей нет" />
      ) : (
        <>
          <div className="admin-table-wrap">
            <table className="admin-table">
              <thead>
                <tr>
                  <th scope="col">Email</th>
                  <th scope="col">Роль</th>
                  <th scope="col">Email подтверждён</th>
                  <th scope="col">Создан</th>
                </tr>
              </thead>
              <tbody>
                {users.data.items.map((user) => (
                  <tr key={user.id}>
                    <td>{user.email}</td>
                    <td>{ROLE_LABELS[user.role]}</td>
                    <td>{user.isEmailVerified ? 'да' : 'нет'}</td>
                    <td>{formatDate(user.createdAt)}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
          <Pager
            page={users.data.page}
            pages={users.data.pages}
            total={users.data.total}
            onPage={setPage}
          />
        </>
      )}
    </section>
  )
}
