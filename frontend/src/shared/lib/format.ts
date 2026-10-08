const rub = new Intl.NumberFormat('ru-RU', {
  style: 'currency',
  currency: 'RUB',
  maximumFractionDigits: 0,
})

export function formatRubRange(from: number, to: number): string {
  if (from === to) return rub.format(from)
  return `${rub.format(from)} – ${rub.format(to)}`
}

const dateTime = new Intl.DateTimeFormat('ru-RU', {
  day: 'numeric',
  month: 'long',
  hour: '2-digit',
  minute: '2-digit',
})

const date = new Intl.DateTimeFormat('ru-RU', { day: 'numeric', month: 'long', year: 'numeric' })

export function formatDateTime(iso: string): string {
  return dateTime.format(new Date(iso))
}

export function formatDate(iso: string): string {
  return date.format(new Date(iso))
}

const number = new Intl.NumberFormat('ru-RU', { maximumFractionDigits: 0 })

/** 350000 → «350 000». */
export function formatNumber(value: number): string {
  return number.format(value)
}

/** Russian plural form for a count: `plural(3, ['кандидат', 'кандидата', 'кандидатов'])`. */
export function plural(count: number, forms: readonly [string, string, string]): string {
  const n = Math.abs(count) % 100
  const last = n % 10
  if (n > 10 && n < 20) return forms[2]
  if (last === 1) return forms[0]
  if (last >= 2 && last <= 4) return forms[1]
  return forms[2]
}
