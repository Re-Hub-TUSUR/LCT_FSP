/** DTOs of the admin API (`/admin/*`, backend `app/admin/schemas.py`). */

export type Period = '7d' | '30d' | '90d' | 'all'
export type TaskKind = 'quiz' | 'code'
export type TaskStatus = 'draft' | 'active' | 'leaked' | 'archived'
export type TaskFlag = 'out_of_target' | 'variant_spread' | 'possible_leak'
export type Block = 'tasks' | 'task_card' | 'platform' | 'employers'
export type CaseStatus = 'flagged' | 'cleared' | 'warned' | 'restricted' | 'blocked'
export type VerificationStatus = 'pending' | 'approved' | 'rejected'
export type EmployerAction = 'clear' | 'warn' | 'restrict' | 'block'

export type Page<T> = {
  items: T[]
  total: number
  page: number
  perPage: number
  pages: number
}

export type AuditEntry = {
  id: string
  entity: string
  entityId: string
  action: string
  changes: Record<string, unknown>
  reason: string | null
  actorEmail: string | null
  createdAt: string
}

// ── Bank ──────────────────────────────────────────────────────────────────────

export type TaskVariable = { name: string; min: number; max: number; step: number }

export type QuizPayload = { options: string[]; correct: number[]; multiple: boolean }
export type CodeGroup = {
  input: string
  expected: string
  hidden: boolean
  /** Share of a hidden test case in the score of the task; 1 by default. */
  weight?: number
}
export type CodePayload = {
  languages: string[]
  timeLimit: number
  groups: CodeGroup[]
  reference?: { language: string; code: string } | null
  /** Compiler id → the program the candidate starts from («найди ошибку»). */
  starter?: Record<string, string>
}

export type AdminTaskRow = {
  id: string
  title: string
  kind: TaskKind
  specializations: string[]
  grade: string | null
  skill: string
  difficulty: 'easy' | 'medium' | 'hard'
  status: TaskStatus
  updatedAt: string
}

export type AdminTaskDetail = AdminTaskRow & {
  statement: string
  variables: TaskVariable[]
  timeLimitMinutes: number | null
  payload: QuizPayload | CodePayload
  createdAt: string
  attempts: number
  canDelete: boolean
  allowedStatuses: TaskStatus[]
  /** What the editor should fix although the task is saved. */
  warnings?: string[]
}

export type AdminTaskWrite = {
  kind: TaskKind
  title: string
  statement: string
  specializations: string[]
  grade: string | null
  skill: string
  difficulty: 'easy' | 'medium' | 'hard'
  variables: TaskVariable[]
  timeLimitMinutes: number | null
  payload: QuizPayload | CodePayload
  status?: 'draft' | 'active'
}

export type BankFilters = {
  page: number
  specialization?: string
  grade?: string
  skill?: string
  kind?: TaskKind
  status?: TaskStatus
  q?: string
}

export type PreviewVariant = {
  values: Record<string, number>
  statement: string
  options: string[]
}

// ── Analytics ─────────────────────────────────────────────────────────────────

export type SnapshotMeta = {
  id: string
  block: Block
  filters: Record<string, string>
  computedAt: string
  durationMs: number
  nextAllowedAt: string
}

export type Metrics = {
  attempts: number
  fullShare: number | null
  partialShare: number | null
  abandonedShare: number | null
  unsolvedShare: number | null
  avgTimeSec: number | null
  medianTimeSec: number | null
}

export type TaskAnalyticsRow = Metrics & {
  taskId: string
  title: string
  kind: TaskKind
  specializations: string[]
  skill: string
  grade: string | null
  status: TaskStatus
  variantSpreadPp: number | null
  maxWeeklyJumpPp: number | null
  flags: TaskFlag[]
}

export type FlagRules = {
  minAttempts: number
  targetMin: number
  targetMax: number
  spreadPp: number
  leakPp: number
}

export type TaskAnalyticsPage = Page<TaskAnalyticsRow> & {
  snapshot: SnapshotMeta | null
  summary: { tasks: number; withAttempts: number; flags: Record<TaskFlag, number> } | null
  rules: FlagRules | null
}

export type TaskCard = {
  taskId: string
  overall: Metrics | null
  flags: TaskFlag[]
  variantSpreadPp: number | null
  maxWeeklyJumpPp: number | null
  variants: (Metrics & { variant: string })[]
  grades: (Metrics & { grade: string | null })[]
  weekly: (Metrics & { week: string })[]
  monthly: (Metrics & { month: string })[]
  histogram: { minute: number; count: number }[]
  /** Questions only: how often every option was picked. Absent in older snapshots. */
  options?: { text: string; correct: boolean; picks: number; share: number | null }[] | null
}

export type FunnelStep = {
  step: string
  label: string
  count: number | null
  fromStartShare: number | null
  fromPreviousShare: number | null
}

export type DemandRow = {
  specialization: string
  specializationLabel: string
  grade: string
  gradeLabel: string
  searches: number | null
  vacancies: number
  invitations: number
  candidates: number
  demand: number
  deficit: number | null
  shortage: boolean
}

export type GradeTestRow = {
  grade: string
  gradeLabel: string
  started: number
  /** Passed, failed or expired: a result is known. */
  settled: number
  passed: number
  /** Percent of the settled ones. */
  passShare: number | null
  /** Tests whose variant needed a rule of the template widened. */
  widened: number
  /** Settled tests of a grade above the one the candidate had already confirmed. */
  stepUp?: number
  stepUpPassed?: number
  stepUpPassShare?: number | null
}

export type PlatformResult = {
  candidateFunnel: FunnelStep[]
  employerFunnel: FunnelStep[]
  demand: DemandRow[]
  /** Absent in snapshots calculated before the block appeared. */
  gradeTests?: {
    grades: GradeTestRow[]
    /** The most frequent cases of the bank running short of tasks for a template. */
    shortages: { note: string; count: number }[]
  }
  missing: string[]
}

export type Snapshot<T> = { snapshot: SnapshotMeta | null; result: T | null }

export type EmployerSignalRow = {
  companyId: string
  name: string
  signals: string[]
  invitesTotal: number
  invitesMaxPerDay: number
  invitesMedianPerDay: number | null
  inbound: number
  answered: number
  responseShare: number | null
  caseStatus: CaseStatus | null
  inviteLimit: number | null
}

export type EmployerSignalsPage = Page<EmployerSignalRow> & {
  snapshot: SnapshotMeta | null
  summary: {
    companies: number
    flagged: number
    invitesSpike: number
    lowResponse: number
    medianInvitesPerDay: number | null
  } | null
  unavailable: string[]
}

// ── Employers ─────────────────────────────────────────────────────────────────

export type EmployerCard = {
  companyId: string
  name: string
  industry: string | null
  city: string | null
  website: string | null
  contactEmail: string | null
  ownerEmail: string
  registeredAt: string
  case: { status: CaseStatus; inviteLimit: number | null; updatedAt: string } | null
  verification: VerificationStatus | null
  banned: boolean
  signals: Omit<EmployerSignalRow, 'caseStatus' | 'inviteLimit'> | null
  liveSignals: { code: string; hits: number; firstAt: string; lastAt: string }[]
  snapshot: SnapshotMeta | null
  vacancies: {
    id: string
    title: string
    specialization: string
    grade: string
    publishedAt: string | null
    createdAt: string
  }[]
  outreach: {
    kind: 'like' | 'invitation' | 'test'
    candidateId: string
    candidateName: string
    status: string | null
    createdAt: string
  }[]
  history: AuditEntry[]
}

export type BanEntry = {
  id: string
  companyId: string | null
  companyName: string | null
  inn: string | null
  email: string | null
  emailDomain: string | null
  reason: string
  isActive: boolean
  createdAt: string
  createdByEmail: string | null
  unbannedAt: string | null
  unbannedByEmail: string | null
  unbanReason: string | null
  accounts: { email: string; role: string }[]
}

export type BanCreate = {
  companyName?: string
  inn?: string
  email?: string
  emailDomain?: string
  reason: string
}

// ── Dictionaries and parameters ───────────────────────────────────────────────

export type Dictionaries = {
  specializations: { code: string; label: string; isArchived: boolean; inPlatform: boolean }[]
  grades: { code: string; label: string; base: string }[]
  skills: { id: string; specializationCode: string; name: string; isArchived: boolean }[]
}

export type Parameter = {
  key: string
  label: string
  value: number
  default: number
  minimum: number
  maximum: number
  unit: string
  updatedAt: string | null
}

export type Parameters = {
  items: Parameter[]
  hardcoded: { parameter: string; where: string }[]
}

// ── Company verification ──────────────────────────────────────────────────────

export type CompanyDocument = {
  id: string
  filename: string
  sizeBytes: number
  uploadedAt: string
  /** A PDF opens in the viewer, a DOCX downloads. */
  kind: 'pdf' | 'docx'
}

export type VerificationRow = {
  companyId: string
  companyName: string
  ownerEmail: string
  status: VerificationStatus
  submittedAt: string
  decidedAt: string | null
  documents: number
}

export type VerificationDetail = VerificationRow & {
  industry: string | null
  city: string | null
  website: string | null
  contactEmail: string | null
  decisionReason: string | null
  decidedByEmail: string | null
  files: CompanyDocument[]
  history: AuditEntry[]
}
