import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import { DECISION_VIEW_LABELS, DECISION_VIEWS, vacancyQueries } from '@/entities/vacancy'
import type { DecisionView } from '@/entities/vacancy'
import { ROUTES } from '@/shared/config'
import './decision-counters.css'

type Props = {
  /** A candidate decides on vacancies, an employer on candidates. */
  role: 'candidate' | 'employer'
}

/** A candidate's like is a response to the vacancy: «Отклики», not «Отобрано». */
const labelOf = (view: DecisionView, role: Props['role']) =>
  role === 'candidate' && view === 'liked' ? 'Отклики' : DECISION_VIEW_LABELS[view]

function useDecisionCounts(role: Props['role']) {
  const vacancies = useQuery({ ...vacancyQueries.reactionCounts(), enabled: role === 'candidate' })
  const candidates = useQuery({
    ...candidateQueries.reactionCounts(),
    enabled: role === 'employer',
  })
  return (role === 'employer' ? candidates : vacancies).data
}

/**
 * Three numbers above the reel: how much is liked, matched and skipped. Each opens that list
 * on «Мои отклики». They refresh after every decision.
 */
export function DecisionCounters({ role }: Props) {
  const counts = useDecisionCounts(role)

  return (
    <nav className="decisions" aria-label="Мои решения">
      {DECISION_VIEWS.map((view) => (
        <Link
          key={view}
          className={`decisions__link decisions__link--${view}`}
          to={`${ROUTES.responses}?tab=${view}`}
        >
          {labelOf(view, role)}
          {counts && <span className="decisions__count">{counts[view]}</span>}
        </Link>
      ))}
    </nav>
  )
}
