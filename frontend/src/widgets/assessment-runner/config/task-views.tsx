import type { AttemptTaskDto, TaskAnswerDto, TaskKind } from '@/entities/assessment'
import { OpenAnswer } from '@/features/answer-open'
import { QuizQuestion } from '@/features/answer-quiz'
import { CodeTask } from '@/features/solve-code-task'

/**
 * Registry of task kinds for the runner. A new kind is added here (how it is saved, marked in
 * the navigation, counted as answered and rendered); the runner itself stays the same.
 */
type KindTraits = {
  /** `instant`: saved on every change; `draft`: typed text, saved after a pause. */
  save: 'instant' | 'draft'
  /** Mark in the task navigation instead of the task number. */
  mark?: string
}

export const TASK_TRAITS: Record<TaskKind, KindTraits> = {
  quiz: { save: 'instant' },
  code: { save: 'draft', mark: '</>' },
  open: { save: 'draft', mark: '¶' },
}

export function isAnswered(task: AttemptTaskDto, answer: TaskAnswerDto | undefined): boolean {
  if (!answer) return false
  switch (task.kind) {
    case 'quiz':
      return (answer as NonNullable<typeof task.answer>).selected.length > 0
    case 'code':
      return true
    case 'open':
      return (answer as NonNullable<typeof task.answer>).text.trim().length > 0
  }
}

type Props = {
  task: AttemptTaskDto
  answer: TaskAnswerDto | undefined
  disabled: boolean
  onChange: (answer: TaskAnswerDto) => void
  onPaste: () => void
  /** What only code tasks need. */
  attemptId: string
  runsLeft: number
  runnerAvailable: boolean
  onRunsLeft: (runsLeft: number) => void
}

/** The answers of one attempt are keyed by task, so an answer always has its task's shape. */
export function TaskView({ task, answer, disabled, onChange, onPaste, ...code }: Props) {
  switch (task.kind) {
    case 'quiz':
      return (
        <QuizQuestion
          task={task}
          answer={(answer as typeof task.answer) ?? null}
          disabled={disabled}
          onChange={onChange}
        />
      )
    case 'code':
      return (
        <CodeTask
          task={task}
          answer={(answer as typeof task.answer) ?? null}
          disabled={disabled}
          onChange={onChange}
          onPaste={onPaste}
          {...code}
        />
      )
    case 'open':
      return (
        <OpenAnswer
          task={task}
          answer={(answer as typeof task.answer) ?? null}
          disabled={disabled}
          onChange={onChange}
          onPaste={onPaste}
        />
      )
  }
}
