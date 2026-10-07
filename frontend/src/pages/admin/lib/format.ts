import { ApiError } from '@/shared/api'

const stamp = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
  hour: '2-digit',
  minute: '2-digit',
})

const dateOnly = new Intl.DateTimeFormat('ru-RU', {
  day: '2-digit',
  month: '2-digit',
  year: 'numeric',
})

const shortDate = new Intl.DateTimeFormat('ru-RU', { day: '2-digit', month: 'short' })
const monthName = new Intl.DateTimeFormat('ru-RU', { month: 'short', year: 'numeric' })

/** «ДД.ММ.ГГГГ ЧЧ:ММ», the stamp of a snapshot. */
export function formatStamp(iso: string): string {
  return stamp.format(new Date(iso)).replace(',', '')
}

export function formatDay(iso: string): string {
  return dateOnly.format(new Date(iso))
}

/** A week label from its Monday (YYYY-MM-DD). */
export function formatWeek(day: string): string {
  return shortDate.format(new Date(`${day}T00:00:00`))
}

export function formatMonth(day: string): string {
  return monthName.format(new Date(`${day}T00:00:00`))
}

export function formatPercent(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${value.toLocaleString('ru-RU', { maximumFractionDigits: 1 })}%`
}

export function formatPp(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return `${value.toLocaleString('ru-RU', { maximumFractionDigits: 1 })} п.п.`
}

export function formatNumber(value: number | null | undefined): string {
  if (value === null || value === undefined) return '—'
  return value.toLocaleString('ru-RU')
}

/** Seconds as «12 мин 05 с» / «1 ч 02 мин». */
export function formatDuration(seconds: number | null | undefined): string {
  if (seconds === null || seconds === undefined) return '—'
  const total = Math.round(seconds)
  const hours = Math.floor(total / 3600)
  const minutes = Math.floor((total % 3600) / 60)
  const rest = total % 60
  if (hours) return `${hours} ч ${String(minutes).padStart(2, '0')} мин`
  if (minutes) return `${minutes} мин ${String(rest).padStart(2, '0')} с`
  return `${rest} с`
}

export function formatBytes(bytes: number): string {
  if (bytes < 1024) return `${bytes} Б`
  if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(0)} КБ`
  return `${(bytes / 1024 / 1024).toFixed(1)} МБ`
}

type ValidationDetail = { loc?: unknown[]; msg?: string }

/** The backend's own message: admins need the exact reason, not a generic one. */
export function errorText(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.status === 0) return error.message
    if (error.status === 403) return 'Недостаточно прав.'
    if (error.code === 'validation_error' && Array.isArray(error.details)) {
      const problems = (error.details as ValidationDetail[])
        .map((item) => item.msg?.replace(/^Value error, /, ''))
        .filter(Boolean)
      if (problems.length) return problems.join('; ')
    }
    return error.message
  }
  if (error instanceof Error) return error.message
  return 'Что-то пошло не так.'
}

/** When the next recalculation is allowed, for a 429 answer. */
export function retryAfter(error: unknown): string | null {
  if (!(error instanceof ApiError) || error.status !== 429) return null
  const details = error.details as { nextAllowedAt?: string } | null
  return details?.nextAllowedAt ?? null
}

/** «Junior+», the label of an 11-level grade code. */
export function gradeLabel(code: string | null, grades: { code: string; label: string }[]): string {
  if (!code) return '—'
  return grades.find((grade) => grade.code === code)?.label ?? code
}
