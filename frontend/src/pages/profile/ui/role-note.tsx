import { ROUTES } from '@/shared/config'
import { ButtonLink, Page } from '@/shared/ui'

export function RoleNote({ title, text }: { title: string; text: string }) {
  return (
    <Page className="page--inset" title={title} lead={text}>
      <ButtonLink to={ROUTES.profile} variant="ghost">
        В кабинет
      </ButtonLink>
    </Page>
  )
}
