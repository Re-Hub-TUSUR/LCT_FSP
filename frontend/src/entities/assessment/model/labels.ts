import type {
  AssessmentAttemptDto,
  AssessmentAttemptStatus,
  AssessmentStatus,
  AssignmentStatus,
  TaskDifficulty,
  TaskKind,
  Verdict,
} from '../api/assessment-api'

export const ASSESSMENT_STATUS_LABELS: Record<AssessmentStatus, string> = {
  passed: 'Тест пройден',
  failed: 'Тест не пройден',
  not_taken: 'Тест ещё не проходил',
}

export const ATTEMPT_STATUS_LABELS: Record<AssessmentAttemptStatus, string> = {
  in_progress: 'Идёт',
  passed: 'Пройден',
  failed: 'Не пройден',
  expired: 'Время вышло',
  awaiting_review: 'Ждёт проверки',
  grading: 'Проверяется',
  interview: 'Собеседование с ИИ',
}

const FAILED_BY_LABELS: Record<NonNullable<AssessmentAttemptDto['failedBy']>, string> = {
  score: 'Не пройден',
  quiz: 'Не пройден: мало верных ответов на вопросы',
  interview: 'Тест пройден, ИИ-собеседование — нет',
}

/** «Не пройден» with 100 points needs the reason: the quiz minimum or the AI interview. */
export function attemptResultLabel(attempt: AssessmentAttemptDto): string {
  if (attempt.status === 'failed' && attempt.failedBy) return FAILED_BY_LABELS[attempt.failedBy]
  return ATTEMPT_STATUS_LABELS[attempt.status]
}

export const ASSIGNMENT_STATUS_LABELS: Record<AssignmentStatus, string> = {
  sent: 'Отправлено',
  in_progress: 'Выполняется',
  review: 'Ждёт проверки',
  done: 'Проверено',
  declined: 'Отклонено',
  expired: 'Срок истёк',
}

export const TASK_KIND_LABELS: Record<TaskKind, string> = {
  quiz: 'Вопрос',
  code: 'Код',
  open: 'Открытый ответ',
}

/** For «what the test consists of»: the label is followed by a count. */
export const TASK_KIND_COUNT_LABELS: Record<TaskKind, string> = {
  quiz: 'вопросов с выбором ответа',
  code: 'задач на код',
  open: 'вопросов с развёрнутым ответом',
}

export const DIFFICULTY_LABELS: Record<TaskDifficulty, string> = {
  easy: 'Лёгкая',
  medium: 'Средняя',
  hard: 'Сложная',
}

export const VERDICT_LABELS: Record<Verdict, string> = {
  ok: 'Верно',
  wrong_answer: 'Неверный ответ',
  runtime_error: 'Ошибка компиляции или выполнения',
  time_limit: 'Превышено время',
}

/** Compiler ids of the code runner; the server sends the allowed subset with every code task. */
export const LANGUAGES: { id: string; label: string }[] = [
  { id: 'python-3.14', label: 'Python 3.14' },
  { id: 'typescript-deno', label: 'TypeScript (Deno)' },
  { id: 'openjdk-25', label: 'Java 25' },
  { id: 'g++-15', label: 'C++ (G++ 15)' },
  { id: 'gcc-15', label: 'C (GCC 15)' },
  { id: 'dotnet-csharp-9', label: 'C# (.NET 9)' },
  { id: 'go-1.26', label: 'Go 1.26' },
  { id: 'rust-1.93', label: 'Rust 1.93' },
  { id: 'php-8.5', label: 'PHP 8.5' },
  { id: 'ruby-4.0', label: 'Ruby 4.0' },
  { id: 'haskell-9.12', label: 'Haskell (GHC 9.12)' },
  { id: 'dotnet-fsharp-9', label: 'F# (.NET 9)' },
]

const TOPIC_LABELS: Record<string, string> = {
  algorithms: 'Алгоритмы',
  git: 'Git',
  sql: 'SQL',
  networks: 'Сети',
  os: 'Операционные системы',
  testing: 'Тестирование',
  security: 'Безопасность',
  appsec: 'Безопасность приложений',
  architecture: 'Архитектура',
  management: 'Управление командой',
  strings: 'Строки',
  logs: 'Журналы и события',
  debugging: 'Поиск ошибки в коде',
  statistics: 'Статистика',
  data: 'Обработка данных',
  graphs: 'Графы',
  'dynamic-programming': 'Динамическое программирование',
  backend: 'Backend',
  frontend: 'Frontend',
  fullstack: 'Fullstack',
  mobile: 'Мобильная разработка',
  'data-science': 'Data Science',
  'data-engineering': 'Data Engineering',
  devops: 'DevOps',
  qa: 'QA',
  gamedev: 'Разработка игр',
}

/** Topics are free-form codes: authors may add their own, those are shown as written. */
export const topicLabel = (topic: string) => TOPIC_LABELS[topic] ?? topic
