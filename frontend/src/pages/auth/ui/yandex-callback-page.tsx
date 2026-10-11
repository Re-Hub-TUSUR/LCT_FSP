import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearchParams } from 'react-router'
import { sessionApi, sessionStore } from '@/entities/session'
import { getErrorMessage } from '@/shared/api'
import { ROUTES } from '@/shared/config'
import { Loader, Page } from '@/shared/ui'

const exchanged = new Set<string>()

/** Yandex returns here with `code` and `state`. A new account continues into the profile form. */
export function YandexCallbackPage() {
  const [params] = useSearchParams()
  const navigate = useNavigate()
  const [failure, setFailure] = useState('')
  const code = params.get('code')
  const state = params.get('state')
  const incomplete = Boolean(params.get('error') || !code || !state)
  const message = failure || (incomplete ? 'Вход через Яндекс не завершён. Начните заново.' : '')

  useEffect(() => {
    if (!code || !state || params.get('error')) return
    if (exchanged.has(code)) return
    exchanged.add(code)
    void sessionApi
      .yandexCallback({ code, state })
      .then((token) => {
        sessionStore.set({ accessToken: token.accessToken, user: token.user })
        const setup = token.user.role === 'employer' ? ROUTES.profileCompany : ROUTES.profileResume
        const home = token.user.role === 'admin' ? ROUTES.admin : ROUTES.feed
        navigate(token.created ? setup : home, { replace: true })
      })
      .catch((error: unknown) => {
        exchanged.delete(code)
        setFailure(getErrorMessage(error))
      })
  }, [code, navigate, params, state])

  if (message) {
    return (
      <Page className="page--auth" title="Вход через Яндекс" lead={message}>
        <Link to={ROUTES.auth}>К выбору роли</Link>
      </Page>
    )
  }

  return (
    <Page className="page--auth" title="Вход через Яндекс" lead="Подтверждаем вход.">
      <Loader />
    </Page>
  )
}
