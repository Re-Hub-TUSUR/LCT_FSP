import { Link } from 'react-router'
import { CHAPTERS } from '../config/chapters'
import './landing-chapters.css'

export function LandingChapters() {
  return (
    <div className="chapters">
      {CHAPTERS.map((chapter, index) => {
        const fromRight = index % 2 === 0
        return (
          <section
            key={chapter.id}
            id={chapter.id}
            className={fromRight ? 'chapter chapter--rtl' : 'chapter chapter--ltr'}
            aria-labelledby={`${chapter.id}-title`}
          >
            <div className={fromRight ? 'chapter__copy' : 'chapter__copy chapter__copy--end'}>
              <div className="chapter__reveal chapter__reveal--1">
                <p className="chapter__index">{chapter.index}</p>
                <p className="chapter__kicker">{chapter.kicker}</p>
                <h2 id={`${chapter.id}-title`} tabIndex={-1}>
                  {chapter.title}
                </h2>
              </div>
              <p className="chapter__lead chapter__reveal chapter__reveal--2">{chapter.lead}</p>
              <div className="chapter__reveal chapter__reveal--3">
                <ul className="chapter__points">
                  {chapter.points.map((point) => (
                    <li key={point.label}>
                      <span>{point.label}</span>
                      {point.text}
                    </li>
                  ))}
                </ul>
                {chapter.links ? (
                  <div className="chapter__links">
                    {chapter.links.map((link) => (
                      <Link key={link.to} className="chapter__link" to={link.to}>
                        {link.label}
                      </Link>
                    ))}
                  </div>
                ) : null}
              </div>
            </div>
          </section>
        )
      })}
    </div>
  )
}
