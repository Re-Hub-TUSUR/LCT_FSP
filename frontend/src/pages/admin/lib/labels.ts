import type {
  CaseStatus,
  EmployerAction,
  Period,
  TaskFlag,
  TaskKind,
  TaskStatus,
  VerificationStatus,
} from '../api/types'

export const PERIOD_LABELS: Record<Period, string> = {
  '7d': '7 дней',
  '30d': '30 дней',
  '90d': '90 дней',
  all: 'Всё время',
}

export const KIND_LABELS: Record<TaskKind, string> = { quiz: 'Тест', code: 'Код' }

export const STATUS_LABELS: Record<TaskStatus, string> = {
  draft: 'Черновик',
  active: 'Активен',
  leaked: 'Утёк',
  archived: 'В архиве',
}

export const DIFFICULTY_LABELS = { easy: 'Лёгкая', medium: 'Средняя', hard: 'Сложная' } as const

export const FLAG_LABELS: Record<TaskFlag, string> = {
  out_of_target: 'Вне целевой сложности',
  variant_spread: 'Разброс вариантов',
  possible_leak: 'Возможная утечка',
}

export const SIGNAL_LABELS: Record<string, string> = {
  invites_spike: 'Аномально много приглашений за сутки',
  low_response: 'Низкая доля ответов кандидатам',
  reaction_flapping: 'Частая смена отметки одного кандидата',
  requisites_churn: 'Частая смена реквизитов',
  junk_vacancies: 'Вакансии без слов',
  meeting_churn: 'Частые отмены встреч',
  chat_media_spam: 'Много файлов в чате',
  invalid_industry: 'Направление не из списка',
}

export const ACCOUNT_ROLE_LABELS: Record<string, string> = {
  candidate: 'Специалист',
  employer: 'Работодатель',
  admin: 'Администратор',
}

export const CASE_LABELS: Record<CaseStatus, string> = {
  flagged: 'Под подозрением',
  cleared: 'Подозрение снято',
  warned: 'Предупреждена',
  restricted: 'Ограничена',
  blocked: 'Заблокирована',
}

export const ACTION_LABELS: Record<EmployerAction, string> = {
  clear: 'Снять подозрение',
  warn: 'Предупредить',
  restrict: 'Ограничить',
  block: 'Заблокировать',
}

export const VERIFICATION_LABELS: Record<VerificationStatus, string> = {
  pending: 'На проверке',
  approved: 'Подтверждена',
  rejected: 'Отклонена',
}

/** Journal actions as they read in the history lists. */
export const AUDIT_ACTION_LABELS: Record<string, string> = {
  create: 'Создание',
  update: 'Изменение',
  status: 'Смена статуса',
  delete: 'Удаление',
  ban: 'Блокировка',
  unban: 'Разблокировка',
  approve: 'Подтверждение',
  reject: 'Отклонение',
  ...ACTION_LABELS,
}

export const AUDIT_ENTITY_LABELS: Record<string, string> = {
  task: 'Задание',
  parameter: 'Параметр',
  specialization: 'Специализация',
  skill: 'Навык',
  company: 'Компания',
  banlist: 'Банлист',
  verification: 'Проверка компании',
}

export const OUTREACH_LABELS = {
  like: 'Лайк',
  invitation: 'Приглашение',
  test: 'Тестовое',
} as const
