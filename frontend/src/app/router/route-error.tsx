import { isRouteErrorResponse, Link, useRouteError } from 'react-router'
import { ROUTES } from '@/shared/config'
import { ErrorState, Page } from '@/shared/ui'

/** Last-resort boundary for render errors and failed lazy chunks. */
export function RouteError() {
  const error = useRouteError()
  const message = isRouteErrorResponse(error)
    ? `${error.status} ${error.statusText}`
    : error instanceof Error
      ? error.message
      : 'Неизвестная ошибка'

  if (import.meta.env.DEV) console.error(error)

  return (
    <Page title="Что-то пошло не так">
      <ErrorState message={message} onRetry={() => window.location.reload()} />
      <Link to={ROUTES.landing}>На главную</Link>
    </Page>
  )
}
