import type { BankTaskDto, BankTaskWrite, TaskDifficulty, TaskKind } from '@/entities/assessment'
import { KIND_EDITORS } from './kinds'
import type { KindDrafts } from './kinds'

const MAX_TITLE = 200

/** Common fields plus the content of the kind being edited (the other drafts stay empty). */
export type TaskFormValues = KindDrafts & {
  kind: TaskKind
  difficulty: TaskDifficulty
  topic: string
  title: string
  statement: string
  specializations: string[]
  isActive: boolean
}

export function toFormValues(kind: TaskKind, task?: BankTaskDto): TaskFormValues {
  return {
    kind,
    difficulty: task?.difficulty ?? 'easy',
    topic: task?.topic ?? '',
    title: task?.title ?? '',
    statement: task?.statement ?? '',
    specializations: task?.specializations ?? [],
    isActive: task?.isActive ?? true,
    quiz: task?.kind === 'quiz' ? task.payload : KIND_EDITORS.quiz.empty(),
    code:
      task?.kind === 'code'
        ? KIND_EDITORS.code.fromPayload(task.payload)
        : KIND_EDITORS.code.empty(),
    open:
      task?.kind === 'open'
        ? KIND_EDITORS.open.fromPayload(task.payload)
        : KIND_EDITORS.open.empty(),
  }
}

/** First problem that would make the server reject the task, or null. */
export function validateTask(values: TaskFormValues): string | null {
  if (!values.statement.trim()) return 'Заполните условие'
  if (!values.topic.trim()) return 'Укажите тему'
  if (KIND_EDITORS[values.kind].titled && !values.title.trim()) return 'Укажите название задачи'
  switch (values.kind) {
    case 'quiz':
      return KIND_EDITORS.quiz.validate(values.quiz)
    case 'code':
      return KIND_EDITORS.code.validate(values.code)
    case 'open':
      return KIND_EDITORS.open.validate(values.open)
  }
}

export function toPayload(values: TaskFormValues): BankTaskWrite {
  const statement = values.statement.trim()
  const common = {
    difficulty: values.difficulty,
    topic: values.topic.trim(),
    statement,
    specializations: values.specializations,
    isActive: values.isActive,
    title: KIND_EDITORS[values.kind].titled ? values.title.trim() : statement.slice(0, MAX_TITLE),
  }
  switch (values.kind) {
    case 'quiz':
      return { ...common, kind: 'quiz', payload: KIND_EDITORS.quiz.toPayload(values.quiz) }
    case 'code':
      return { ...common, kind: 'code', payload: KIND_EDITORS.code.toPayload(values.code) }
    case 'open':
      return { ...common, kind: 'open', payload: KIND_EDITORS.open.toPayload(values.open) }
  }
}
