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

/** Russian plural form for a count: plural(3, ['вакансия', 'вакансии', 'вакансий']). */
export function plural(count: number, [one, few, many]: readonly [string, string, string]) {
  const tens = Math.abs(count) % 100
  const units = tens % 10
  if (tens > 10 && tens < 20) return many
  if (units === 1) return one
  if (units > 1 && units < 5) return few
  return many
}
