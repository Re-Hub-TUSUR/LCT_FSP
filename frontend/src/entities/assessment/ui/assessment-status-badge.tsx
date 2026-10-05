import type { AssessmentStatus } from '../api/assessment-api'
import { ASSESSMENT_STATUS_LABELS } from '../model/labels'
import './assessment-status-badge.css'

type Props = {
  status: AssessmentStatus
  /** Shown next to "passed": the score of the confirming test. */
  score?: number | null
}

/** The three states an employer sees: passed, failed, never taken. */
export function AssessmentStatusBadge({ status, score }: Props) {
  return (
    <span className={`assessment-badge assessment-badge--${status}`}>
      {ASSESSMENT_STATUS_LABELS[status]}
      {status === 'passed' && score != null && ` · ${Math.round(score)}/100`}
    </span>
  )
}
