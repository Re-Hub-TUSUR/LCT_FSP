import { useEffect } from 'react'
import './ban-screen.css'

type Props = {
  reason: string
  supportEmail: string
}

/** The only thing a banned person sees: no header, no routes, no way to dismiss it. */
export function BanScreen({ reason, supportEmail }: Props) {
  useEffect(() => {
    document.getElementById('splash')?.remove()
  }, [])

  return (
    <div className="ban-screen">
      <div className="ban-screen__card" role="dialog" aria-modal="true" aria-labelledby="ban-title">
        <p className="ban-screen__mark" aria-hidden="true">
          X_X
        </p>
        <h1 id="ban-title" className="ban-screen__title">
          Вы были забанены по следующей причине: {reason}.
        </h1>
        <p className="ban-screen__text">
          Если вы думаете, что вас забанили по ошибке, можете попробовать написать нам на эту почту:{' '}
          {supportEmail ? <a href={`mailto:${supportEmail}`}>{supportEmail}</a> : supportEmail}
        </p>
      </div>
    </div>
  )
}
