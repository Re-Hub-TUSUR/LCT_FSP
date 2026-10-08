import { useMutation, useQueryClient } from '@tanstack/react-query'
import { useEffect, useRef } from 'react'
import { useNavigate, useSearchParams } from 'react-router'
import { candidateApi, candidateKeys } from '@/entities/candidate'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { ButtonLink, ErrorState, Loader, Page } from '@/shared/ui'

/** FSP ID returns here with `code` and `state` (or `error`); the backend finishes the link. */
export function FspCallbackPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const code = params.get('code')
  const state = params.get('state')
  const denied = params.get('error')
  const started = useRef(false)

  const link = useMutation({
    mutationFn: candidateApi.linkFsp,
    onSuccess: (profile) => {
      queryClient.setQueryData(candidateKeys.mine(), profile)
      void navigate(`${ROUTES.profileSettings}?fsp=linked`, { replace: true })
    },
  })
  const { mutate } = link

  useEffect(() => {
    // A code is single-use: StrictMode's second effect run must not send it again.
    if (started.current || !code || !state) return
    started.current = true
    mutate({ code, state })
  }, [code, state, mutate])

  let body
  if (denied) {
    body = (
      <ErrorState
        title="Вход через ФСП ID отменён"
        message="Профиль не связан. Привязать ФСП ID можно в настройках в любой момент."
      />
    )
  } else if (!code || !state) {
    body = (
      <ErrorState
        title="Ссылка неполная"
        message="ФСП ID не вернул код входа. Начните привязку заново из настроек."
      />
    )
  } else if (link.isError) {
    body = <ErrorState title="Не удалось привязать ФСП ID" message={getErrorMessage(link.error)} />
  } else {
    body = <Loader label="Получаем данные из ФСП…" />
  }

  const finished = Boolean(denied) || !code || !state || link.isError

  return (
    <Page className="page--inset" title="ФСП ID">
      {body}
      {finished && (
        <div>
          <ButtonLink to={ROUTES.profileSettings} variant="ghost">
            Вернуться в настройки
          </ButtonLink>
        </div>
      )}
    </Page>
  )
}
