import type { ReactNode } from 'react'
import './page.css'

type PageProps = {
  title: string
  lead?: ReactNode
  actions?: ReactNode
  children?: ReactNode
  className?: string
}

export function Page({ title, lead, actions, children, className }: PageProps) {
  return (
    <section className={className ? `page ${className}` : 'page'} aria-labelledby="page-title">
      <header className="page__header">
        <div>
          <h1 id="page-title" className="page__title">
            {title}
          </h1>
          {lead && <p className="page__lead">{lead}</p>}
        </div>
        {actions && <div className="page__actions">{actions}</div>}
      </header>
      <div className="page__body">{children}</div>
    </section>
  )
}

export function Section({ title, children }: { title: string; children?: ReactNode }) {
  return (
    <section className="page-section">
      <h2 className="page-section__title">{title}</h2>
      {children}
    </section>
  )
}

export function Tag({ children }: { children: ReactNode }) {
  return <span className="tag">{children}</span>
}
