import { useMutation, useQueryClient } from '@tanstack/react-query'
import { assessmentKeys, assignmentApi, assignmentKeys } from '@/entities/assessment'
import type { AssignmentDto } from '@/entities/assessment'
import { getErrorMessage } from '@/shared/api'
import { Button } from '@/shared/ui'
import './assignment-actions.css'

/** Candidate's answer to a test a company sent: start it now or refuse. */
export function AssignmentActions({ assignment }: { assignment: AssignmentDto }) {
  const queryClient = useQueryClient()
  const refresh = () => queryClient.invalidateQueries({ queryKey: assignmentKeys.incoming() })

  const start = useMutation({
    mutationFn: () => assignmentApi.start(assignment.id),
    onSuccess: (attempt) => {
      // The testing page switches to the runner as soon as the status names the attempt.
      queryClient.setQueryData(assessmentKeys.attempt(attempt.id), attempt)
      void queryClient.invalidateQueries({ queryKey: assessmentKeys.status() })
      void refresh()
    },
  })
  const decline = useMutation({
    mutationFn: () => assignmentApi.decline(assignment.id),
    onSuccess: () => void refresh(),
  })
  const error = start.error ?? decline.error
  const busy = start.isPending || decline.isPending

  return (
    <div className="assignment-actions">
      <Button size="inline" disabled={busy} onClick={() => start.mutate()}>
        {start.isPending ? 'Готовим…' : 'Начать'}
      </Button>
      <Button variant="ghost" size="inline" disabled={busy} onClick={() => decline.mutate()}>
        Отказаться
      </Button>
      {error && (
        <p className="assignment-actions__error" role="alert">
          {getErrorMessage(error)}
        </p>
      )}
    </div>
  )
}
