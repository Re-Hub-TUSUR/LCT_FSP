import type { ReactNode } from 'react'
import { isHttpUrl } from '@/shared/lib'
import { Tag } from '@/shared/ui'
import type { CompanyDto } from '../api/company-api'
import './company-card.css'

export function CompanyCard({ company, actions }: { company: CompanyDto; actions?: ReactNode }) {
  return (
    <article className="company-card" aria-label={company.name}>
      <header className="company-card__header">
        <h3 className="company-card__name">{company.name}</h3>
        {company.industry && <Tag>{company.industry}</Tag>}
      </header>
      {company.description && <p className="company-card__text">{company.description}</p>}
      {company.website && isHttpUrl(company.website) && (
        <a className="company-card__link" href={company.website} target="_blank" rel="noreferrer">
          {company.website}
        </a>
      )}
      {actions && <footer className="company-card__actions">{actions}</footer>}
    </article>
  )
}
