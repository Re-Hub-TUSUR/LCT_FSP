import { useQuery } from '@tanstack/react-query'
import { Link, useSearchParams } from 'react-router'
import { candidateQueries } from '@/entities/candidate'
import {
  DECISION_VIEW_LABELS,
  DECISION_VIEWS,
  parseListView,
  vacancyQueries,
} from '@/entities/vacancy'
import type { ListView } from '@/entities/vacancy'
import { ROUTES } from '@/shared/config'
import { Tabs } from '@/shared/ui'
import type { TabItem } from '@/shared/ui'
import './decision-counters.css'

type Props = {
  /** A candidate decides on vacancies, an employer on candidates. */
  role: 'candidate' | 'employer'
}

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
 * in the feed. They refresh after every decision.
 */
export function DecisionCounters({ role }: Props) {
  const counts = useDecisionCounts(role)

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

const TONES = { liked: undefined, matched: 'accent', skipped: 'danger' } as const

/** The feed's views in the page header: everything, or one of the lists of own decisions. */
export function FeedViewTabs({ role }: Props) {
  const counts = useDecisionCounts(role)
  const [params, setParams] = useSearchParams()
  const view = parseListView(params.get('view'))

  const items: TabItem<ListView>[] = [
    { value: 'all', label: 'Все' },
    ...DECISION_VIEWS.map((item) => ({
      value: item,
      label: DECISION_VIEW_LABELS[item],
      count: counts?.[item],
      tone: TONES[item],
    })),
  ]

  return (
    <Tabs
      label="Показать"
      items={items}
      value={view}
      onChange={(next) => {
        const copy = new URLSearchParams(params)
        copy.delete('page')
        if (next === 'all') copy.delete('view')
        else copy.set('view', next)
        setParams(copy, { replace: true })
      }}
    />
  )
}
