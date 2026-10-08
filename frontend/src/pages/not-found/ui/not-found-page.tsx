import { ROUTES } from '@/shared/config'
import { ButtonLink, Page } from '@/shared/ui'

export function NotFoundPage() {
  return (
    <Page title="Страница не найдена" lead="Проверьте адрес или вернитесь на главную">
      <div>
        <ButtonLink variant="ghost" to={ROUTES.landing}>
          На главную
        </ButtonLink>
      </div>
    </Page>
  )
}
