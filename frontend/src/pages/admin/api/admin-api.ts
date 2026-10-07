import { queryOptions } from '@tanstack/react-query'
import { http } from '@/shared/api'
import type { Paginated } from '@/shared/api'
import type { UserDto } from '@/entities/user'
import type {
  AdminTaskDetail,
  AdminTaskRow,
  AdminTaskWrite,
  AuditEntry,
  BanCreate,
  BanEntry,
  BankFilters,
  Block,
  Dictionaries,
  EmployerAction,
  EmployerCard,
  EmployerSignalsPage,
  Page,
  Parameters,
  Period,
  PlatformResult,
  PreviewVariant,
  Snapshot,
  TaskAnalyticsPage,
  TaskCard,
  TaskStatus,
  TaskVariable,
  VerificationDetail,
  VerificationRow,
  VerificationStatus,
} from './types'

export const ADMIN_PAGE_SIZE = 50

/**
 * Snapshots change only when an admin presses «Пересчитать»: the page never refetches them by
 * itself (no polling, no refetch on focus), the recalculation writes the new one into the cache.
 */
const stored = { staleTime: Number.POSITIVE_INFINITY, refetchOnWindowFocus: false } as const

export type TaskTableQuery = {
  period: Period
  page: number
  flag?: string
  q?: string
  specialization?: string
  kind?: string
}

export type EmployerTableQuery = {
  period: Period
  page: number
  signal?: string
  status?: string
  q?: string
}

export const adminKeys = {
  all: ['admin'] as const,
  bank: () => [...adminKeys.all, 'bank'] as const,
  bankList: (filters: BankFilters) => [...adminKeys.bank(), 'list', filters] as const,
  task: (id: string) => [...adminKeys.bank(), 'task', id] as const,
  taskHistory: (id: string) => [...adminKeys.bank(), 'history', id] as const,
  skills: () => [...adminKeys.bank(), 'skills'] as const,
  analytics: () => [...adminKeys.all, 'analytics'] as const,
  taskTable: (query: TaskTableQuery) => [...adminKeys.analytics(), 'tasks', query] as const,
  employerTable: (query: EmployerTableQuery) =>
    [...adminKeys.analytics(), 'employers', query] as const,
  snapshot: (block: Block, period: Period, taskId?: string) =>
    [...adminKeys.analytics(), 'snapshot', block, period, taskId ?? null] as const,
  employer: (id: string, period: Period) => [...adminKeys.all, 'employer', id, period] as const,
  banlist: (query: { page: number; q?: string; active?: boolean }) =>
    [...adminKeys.all, 'banlist', query] as const,
  banHistory: (id: string) => [...adminKeys.all, 'ban-history', id] as const,
  dictionaries: () => [...adminKeys.all, 'dictionaries'] as const,
  parameters: () => [...adminKeys.all, 'parameters'] as const,
  audit: (query: { page: number; entity?: string }) => [...adminKeys.all, 'audit', query] as const,
  verifications: (query: { page: number; status?: VerificationStatus; q?: string }) =>
    [...adminKeys.all, 'verifications', query] as const,
  verification: (companyId: string) => [...adminKeys.all, 'verification', companyId] as const,
  pendingCount: () => [...adminKeys.all, 'verifications', 'pending-count'] as const,
  users: (page: number) => [...adminKeys.all, 'users', page] as const,
}

export const adminQueries = {
  bankList: (filters: BankFilters) =>
    queryOptions({
      queryKey: adminKeys.bankList(filters),
      queryFn: ({ signal }) =>
        http.get<Page<AdminTaskRow>>('/admin/bank/tasks', { query: filters, signal }),
    }),
  task: (id: string) =>
    queryOptions({
      queryKey: adminKeys.task(id),
      queryFn: ({ signal }) => http.get<AdminTaskDetail>(`/admin/bank/tasks/${id}`, { signal }),
    }),
  taskHistory: (id: string) =>
    queryOptions({
      queryKey: adminKeys.taskHistory(id),
      queryFn: ({ signal }) =>
        http.get<Page<AuditEntry>>(`/admin/bank/tasks/${id}/history`, { signal }),
    }),
  skills: () =>
    queryOptions({
      queryKey: adminKeys.skills(),
      queryFn: ({ signal }) => http.get<string[]>('/admin/bank/skills', { signal }),
    }),
  taskTable: (query: TaskTableQuery) =>
    queryOptions({
      queryKey: adminKeys.taskTable(query),
      queryFn: ({ signal }) =>
        http.get<TaskAnalyticsPage>('/admin/analytics/tasks', { query, signal }),
      ...stored,
    }),
  employerTable: (query: EmployerTableQuery) =>
    queryOptions({
      queryKey: adminKeys.employerTable(query),
      queryFn: ({ signal }) =>
        http.get<EmployerSignalsPage>('/admin/analytics/employers', { query, signal }),
      ...stored,
    }),
  platform: (period: Period) =>
    queryOptions({
      queryKey: adminKeys.snapshot('platform', period),
      queryFn: ({ signal }) =>
        http.get<Snapshot<PlatformResult>>('/admin/analytics/snapshot/platform', {
          query: { period },
          signal,
        }),
      ...stored,
    }),
  taskCard: (taskId: string, period: Period) =>
    queryOptions({
      queryKey: adminKeys.snapshot('task_card', period, taskId),
      queryFn: ({ signal }) =>
        http.get<Snapshot<TaskCard>>('/admin/analytics/snapshot/task_card', {
          query: { period, taskId },
          signal,
        }),
      ...stored,
    }),
  employer: (id: string, period: Period) =>
    queryOptions({
      queryKey: adminKeys.employer(id, period),
      queryFn: ({ signal }) =>
        http.get<EmployerCard>(`/admin/employers/${id}`, { query: { period }, signal }),
    }),
  banlist: (query: { page: number; q?: string; active?: boolean }) =>
    queryOptions({
      queryKey: adminKeys.banlist(query),
      queryFn: ({ signal }) => http.get<Page<BanEntry>>('/admin/banlist', { query, signal }),
    }),
  banHistory: (id: string) =>
    queryOptions({
      queryKey: adminKeys.banHistory(id),
      queryFn: ({ signal }) => http.get<AuditEntry[]>(`/admin/banlist/${id}/history`, { signal }),
    }),
  dictionaries: () =>
    queryOptions({
      queryKey: adminKeys.dictionaries(),
      queryFn: ({ signal }) => http.get<Dictionaries>('/admin/dictionaries', { signal }),
    }),
  parameters: () =>
    queryOptions({
      queryKey: adminKeys.parameters(),
      queryFn: ({ signal }) => http.get<Parameters>('/admin/parameters', { signal }),
    }),
  audit: (query: { page: number; entity?: string }) =>
    queryOptions({
      queryKey: adminKeys.audit(query),
      queryFn: ({ signal }) => http.get<Page<AuditEntry>>('/admin/audit', { query, signal }),
    }),
  verifications: (query: { page: number; status?: VerificationStatus; q?: string }) =>
    queryOptions({
      queryKey: adminKeys.verifications(query),
      queryFn: ({ signal }) =>
        http.get<Page<VerificationRow>>('/admin/verifications', { query, signal }),
    }),
  verification: (companyId: string) =>
    queryOptions({
      queryKey: adminKeys.verification(companyId),
      queryFn: ({ signal }) =>
        http.get<VerificationDetail>(`/admin/verifications/${companyId}`, { signal }),
    }),
  pendingCount: () =>
    queryOptions({
      queryKey: adminKeys.pendingCount(),
      queryFn: ({ signal }) => http.get<number>('/admin/verifications/pending-count', { signal }),
    }),
  users: (page: number) =>
    queryOptions({
      queryKey: adminKeys.users(page),
      queryFn: ({ signal }) =>
        http.get<Paginated<UserDto>>('/admin/users', {
          query: { page, perPage: ADMIN_PAGE_SIZE },
          signal,
        }),
    }),
}

export const adminApi = {
  createTask: (data: AdminTaskWrite) => http.post<AdminTaskDetail>('/admin/bank/tasks', data),
  updateTask: (id: string, data: AdminTaskWrite) =>
    http.put<AdminTaskDetail>(`/admin/bank/tasks/${id}`, data),
  setTaskStatus: (id: string, status: TaskStatus, reason?: string) =>
    http.post<AdminTaskDetail>(`/admin/bank/tasks/${id}/status`, { status, reason }),
  deleteTask: (id: string) => http.delete<void>(`/admin/bank/tasks/${id}`),
  preview: (statement: string, variables: TaskVariable[], options: string[]) =>
    http.post<PreviewVariant[]>('/admin/bank/preview', { statement, variables, options }),
  recalculate: <T>(block: Block, period: Period, taskId?: string) =>
    http.post<Snapshot<T>>(`/admin/analytics/${block}/recalculate`, { period, taskId }),
  decide: (companyId: string, action: EmployerAction, reason: string, inviteLimit?: number) =>
    http.post<EmployerCard>(`/admin/employers/${companyId}/decision`, {
      action,
      reason,
      inviteLimit,
    }),
  addBan: (data: BanCreate) => http.post<BanEntry>('/admin/banlist', data),
  unban: (id: string, reason: string) =>
    http.post<BanEntry>(`/admin/banlist/${id}/unban`, { reason }),
  addSpecialization: (code: string, label: string) =>
    http.post<Dictionaries>('/admin/dictionaries/specializations', { code, label }),
  updateSpecialization: (code: string, data: { label?: string; isArchived?: boolean }) =>
    http.patch<Dictionaries>(`/admin/dictionaries/specializations/${code}`, data),
  addSkill: (specializationCode: string, name: string) =>
    http.post<Dictionaries>('/admin/dictionaries/skills', { specializationCode, name }),
  updateSkill: (id: string, data: { name?: string; isArchived?: boolean }) =>
    http.patch<Dictionaries>(`/admin/dictionaries/skills/${id}`, data),
  setParameter: (key: string, value: number) =>
    http.put<Parameters>(`/admin/parameters/${key}`, { value }),
  approve: (companyId: string, comment?: string) =>
    http.post<VerificationDetail>(`/admin/verifications/${companyId}/approve`, { comment }),
  reject: (companyId: string, reason: string) =>
    http.post<VerificationDetail>(`/admin/verifications/${companyId}/reject`, { reason }),
  documentBlob: (companyId: string, documentId: string) =>
    http.blob(`/admin/verifications/${companyId}/documents/${documentId}`),
}
