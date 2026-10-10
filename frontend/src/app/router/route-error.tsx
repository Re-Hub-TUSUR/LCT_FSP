import { useEffect, useState } from 'react'
import { isRouteErrorResponse, useRouteError } from 'react-router'
import { ROUTES } from '@/shared/config'
import { ButtonLink, ErrorState, Loader, Page } from '@/shared/ui'
import { canReloadForNewBuild, isStaleChunkError, reloadForNewBuild } from './stale-build'

/** Last-resort boundary for render errors and failed lazy chunks. */
export function RouteError() {
  const error = useRouteError()
  const stale = isStaleChunkError(error)
  // The address is already the page that failed to load, so a reload opens it in the new build.
  const [reloading] = useState(() => stale && canReloadForNewBuild())

  useEffect(() => {
    if (reloading) reloadForNewBuild()
  }, [reloading])

  if (import.meta.env.DEV) console.error(error)

  if (reloading) return <Loader />

  const message = stale
    ? 'Сайт обновился, а страница не загрузилась. Проверьте подключение и обновите её.'
    : isRouteErrorResponse(error)
      ? `${error.status} ${error.statusText}`
      : error instanceof Error
        ? error.message
        : 'Неизвестная ошибка'

  return (
    <Page title="Что-то пошло не так">
      <ErrorState message={message} onRetry={() => window.location.reload()} />
      <div>
        <ButtonLink variant="ghost" to={ROUTES.landing}>
          На главную
        </ButtonLink>
      </div>
    </Page>
  )
}
