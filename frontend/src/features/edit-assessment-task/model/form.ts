import type {
  BankTaskDto,
  BankTaskWrite,
  TaskDifficulty,
  TaskKind,
  TestGroupDto,
} from '@/entities/assessment'

/** The code runner cuts stdout at 999 characters, so a longer expected output can never match. */
export const MAX_EXPECTED_OUTPUT = 900
const MAX_TITLE = 200

export type TaskFormValues = {
  kind: TaskKind
  difficulty: TaskDifficulty
  topic: string
  title: string
  statement: string
  specializations: string[]
  isActive: boolean
  // Quiz.
  options: string[]
  correct: number[]
  multiple: boolean
  // Code.
  languages: string[]
  timeLimit: string
  groups: TestGroupDto[]
  referenceLanguage: string
  referenceCode: string
}

const EMPTY_GROUPS: TestGroupDto[] = [
  { input: '', expected: '', hidden: false },
  { input: '', expected: '', hidden: true },
]

export function toFormValues(kind: TaskKind, task?: BankTaskDto): TaskFormValues {
  return {
    kind,
    difficulty: task?.difficulty ?? 'easy',
    topic: task?.topic ?? '',
    title: task?.title ?? '',
    statement: task?.statement ?? '',
    specializations: task?.specializations ?? [],
    isActive: task?.isActive ?? true,
    options: task?.quiz?.options ?? ['', '', '', ''],
    correct: task?.quiz?.correct ?? [0],
    multiple: task?.quiz?.multiple ?? false,
    languages: task?.code?.languages ?? [],
    timeLimit: String(task?.code?.timeLimit ?? 5),
    groups: task?.code?.groups ?? EMPTY_GROUPS,
    referenceLanguage: task?.code?.reference?.language ?? 'python-3.14',
    referenceCode: task?.code?.reference?.code ?? '',
  }
}

/** First problem that would make the server reject the task, or null. */
export function validateTask(values: TaskFormValues): string | null {
  if (!values.statement.trim()) return 'Заполните условие'
  if (!values.topic.trim()) return 'Укажите тему'

  if (values.kind === 'quiz') {
    if (values.options.some((option) => !option.trim())) return 'Заполните все варианты ответа'
    if (values.options.length < 2) return 'Нужно хотя бы два варианта'
    if (values.correct.length === 0) return 'Отметьте верный вариант'
    if (!values.multiple && values.correct.length > 1)
      return 'Несколько верных вариантов возможны только при множественном выборе'
    return null
  }

  if (!values.title.trim()) return 'Укажите название задачи'
  const limit = Number(values.timeLimit)
  if (!(limit > 0 && limit <= 20)) return 'Ограничение времени — от 0 до 20 секунд'
  if (values.groups.some((group) => !group.expected.trim()))
    return 'У каждой группы тестов должен быть ожидаемый вывод'
  if (values.groups.some((group) => group.expected.length > MAX_EXPECTED_OUTPUT))
    return `Ожидаемый вывод группы — не длиннее ${MAX_EXPECTED_OUTPUT} символов`
  const hidden = values.groups.filter((group) => group.hidden).length
  if (hidden === 0 || hidden === values.groups.length)
    return 'Нужна хотя бы одна открытая и одна закрытая группа тестов'
  return null
}

export function toPayload(values: TaskFormValues): BankTaskWrite {
  const statement = values.statement.trim()
  const common = {
    kind: values.kind,
    difficulty: values.difficulty,
    topic: values.topic.trim(),
    statement,
    specializations: values.specializations,
    isActive: values.isActive,
  }
  if (values.kind === 'quiz') {
    return {
      ...common,
      // A question is its own title.
      title: statement.slice(0, MAX_TITLE),
      quiz: {
        options: values.options.map((option) => option.trim()),
        correct: values.correct,
        multiple: values.multiple,
      },
      code: null,
    }
  }
  return {
    ...common,
    title: values.title.trim(),
    quiz: null,
    code: {
      languages: values.languages,
      timeLimit: Number(values.timeLimit),
      groups: values.groups,
      reference: values.referenceCode.trim()
        ? { language: values.referenceLanguage, code: values.referenceCode }
        : null,
    },
  }
}
