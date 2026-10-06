import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import { DECISION_VIEW_LABELS, DECISION_VIEWS, vacancyQueries } from '@/entities/vacancy'
import { ROUTES } from '@/shared/config'
import './decision-counters.css'

type Props = {
  /** A candidate decides on vacancies, an employer on candidates. */
  role: 'candidate' | 'employer'
}

/**
 * One quiet line above the reel: how much is liked, matched and skipped. Each number opens
 * that list in the feed. It refreshes after every decision.
 */
export function DecisionCounters({ role }: Props) {
  const vacancies = useQuery({ ...vacancyQueries.reactionCounts(), enabled: role === 'candidate' })
  const candidates = useQuery({
    ...candidateQueries.reactionCounts(),
    enabled: role === 'employer',
  })
  const counts = (role === 'employer' ? candidates : vacancies).data

  return (
    <nav className="decisions" aria-label="Мои решения">
      {DECISION_VIEWS.map((view) => (
        <Link
          key={view}
          className={`decisions__link decisions__link--${view}`}
          to={`${ROUTES.feed}?view=${view}`}
        >
          {DECISION_VIEW_LABELS[view]}
          {counts && <span className="decisions__count">{counts[view]}</span>}
        </Link>
      ))}
    </nav>
  )
}
