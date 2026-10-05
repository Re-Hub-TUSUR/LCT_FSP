import { Link } from 'react-router'
import { ROUTES } from '@/shared/config'
import { Page } from '@/shared/ui'

export function NotFoundPage() {
  return (
    <Page title="Страница не найдена" lead="Проверьте адрес или вернитесь на главную">
      <Link to={ROUTES.landing}>На главную</Link>
    </Page>
  )
}
