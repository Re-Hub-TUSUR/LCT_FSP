import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { Page } from '@/shared/ui'
import { SiteHeader } from '@/widgets/site-header'
import type { NavItem } from '@/widgets/site-header'
import type { LegalDocument } from '../model/types'
import { LegalBlocks, sectionId } from './legal-blocks'
import './legal-page.css'

const DOCUMENT_LINKS: NavItem[] = [
  { label: 'Политика', to: ROUTES.privacy },
  { label: 'Соглашение', to: ROUTES.terms },
  { label: 'Согласие', to: ROUTES.consent },
]

type Props = {
  document: LegalDocument
  /** The Word version, served from `public/legal`. */
  downloadHref: string
}

/**
 * A legal document as a public page. It lives outside the cabinet layout on purpose: a candidate
 * who has not saved a resume yet is sent to the resume form from every cabinet page, and the
 * consent link on that very form must stay readable.
 */
export function LegalPage({ document, downloadHref }: Props) {
  const { user } = useSession()
  const cta: NavItem = user
    ? { label: 'Кабинет', to: ROUTES.profile }
    : { label: 'Войти', to: ROUTES.auth }

  return (
    <>
      <div className="app-glow" aria-hidden="true" />
      <SiteHeader links={DOCUMENT_LINKS} cta={cta} />
      <main>
        <Page
          className="legal-page"
          title={document.title}
          lead={document.subtitle}
          actions={
            <a className="btn btn--ghost btn--inline" href={downloadHref} download>
              Скачать .docx
            </a>
          }
        >
          <article className="legal-doc">
            <table className="legal-doc__table legal-doc__table--card">
              <tbody>
                {document.meta.map(([label, value]) => (
                  <tr key={label}>
                    <th scope="row">{label}</th>
                    <td>{value}</td>
                  </tr>
                ))}
              </tbody>
            </table>

            <nav className="legal-doc__toc" aria-label="Содержание">
              <strong>Содержание</strong>
              <ol>
                {document.toc.map((title, index) => (
                  <li key={title}>
                    <a href={`#${sectionId(index)}`}>{title}</a>
                  </li>
                ))}
              </ol>
            </nav>

            <LegalBlocks blocks={document.blocks} />
          </article>
        </Page>
      </main>
    </>
  )
}
