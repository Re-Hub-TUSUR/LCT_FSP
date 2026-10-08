import type {
  FspAchievementDto,
  FspDiscipline,
  FspEventKind,
  FspOutcome,
  FspSportTitleDto,
  FspTitleKind,
} from '../api/candidate-api'

export const FSP_DISCIPLINE_LABELS: Record<FspDiscipline, string> = {
  algorithmic: 'алгоритмическое программирование',
  product: 'продуктовое программирование',
  security: 'программирование систем ИБ',
  robotics: 'программирование робототехники',
  uav: 'программирование БАС',
}

export const FSP_EVENT_KIND_LABELS: Record<FspEventKind, string> = {
  championship: 'чемпионат',
  cup: 'кубок',
  hackathon: 'хакатон',
  olympiad: 'олимпиада',
}

export const FSP_OUTCOME_LABELS: Record<FspOutcome, string> = {
  winner: 'победитель',
  prizewinner: 'призёр',
  finalist: 'финалист',
  participant: 'участник',
}

export const FSP_TITLE_LABELS: Record<FspTitleKind, string> = {
  rank_3: '3-й разряд',
  rank_2: '2-й разряд',
  rank_1: '1-й разряд',
  kms: 'КМС',
  ms: 'МС',
  msmk: 'МСМК',
  zms: 'ЗМС',
}

export const FSP_LEVEL_LABELS: Record<FspAchievementDto['level'], string> = {
  regional: 'региональный',
  national: 'всероссийский',
  international: 'международный',
}

const OUTCOME_ORDER: FspOutcome[] = ['winner', 'prizewinner', 'finalist', 'participant']
const TITLE_ORDER: FspTitleKind[] = ['zms', 'msmk', 'ms', 'kms', 'rank_1', 'rank_2', 'rank_3']

/** «Призёр, 2-е место» / «Победитель» / «Участник». */
export function fspOutcomeText(item: FspAchievementDto): string {
  const label = item.result ? FSP_OUTCOME_LABELS[item.result] : undefined
  // A profile saved before the registry fields existed has only a place.
  if (!label) return item.place ? `${item.place}-е место` : 'Участие'
  const text = label.charAt(0).toUpperCase() + label.slice(1)
  return item.place && item.result !== 'winner' ? `${text}, ${item.place}-е место` : text
}

/** «команда «NullPointer»» for team results, empty for individual ones. */
export function fspTeamText(item: FspAchievementDto): string {
  return item.participation === 'team' && item.teamName ? `команда «${item.teamName}»` : ''
}

/** «Призёр, 2-е место · Кубок России · алгоритмическое программирование, 2025 · команда «X»». */
export function fspAchievementLine(item: FspAchievementDto, { detailed = false } = {}): string {
  const parts = [
    fspOutcomeText(item),
    item.eventName,
    `${FSP_DISCIPLINE_LABELS[item.discipline]}, ${item.year}`,
  ]
  const team = fspTeamText(item)
  if (team) parts.push(team)
  if (detailed && item.eventKind) {
    parts.push(`${FSP_EVENT_KIND_LABELS[item.eventKind]}, ${FSP_LEVEL_LABELS[item.level]} уровень`)
  } else if (detailed) {
    parts.push(`${FSP_LEVEL_LABELS[item.level]} уровень`)
  }
  return parts.join(' · ')
}

/** «КМС · алгоритмическое программирование, 2025». */
export function fspTitleLine(title: FspSportTitleDto): string {
  return `${FSP_TITLE_LABELS[title.kind]} · ${FSP_DISCIPLINE_LABELS[title.discipline]}, ${title.awardedYear}`
}

function outcomeRank(item: FspAchievementDto): number {
  if (item.result) return OUTCOME_ORDER.indexOf(item.result)
  if (item.place === 1) return 0
  if (item.place != null && item.place <= 3) return 1
  if (item.place != null) return 2
  return 3
}

export function bestFspResult(
  items: FspAchievementDto[] | undefined,
): FspAchievementDto | undefined {
  // oxlint-disable-next-line unicorn/no-array-sort -- a copy is sorted; toSorted() needs ES2023
  return [...(items ?? [])].sort(
    (a, b) =>
      outcomeRank(a) - outcomeRank(b) || (a.place ?? 99) - (b.place ?? 99) || b.year - a.year,
  )[0]
}

export function bestFspTitle(items: FspSportTitleDto[] | undefined): FspSportTitleDto | undefined {
  // oxlint-disable-next-line unicorn/no-array-sort -- a copy is sorted; toSorted() needs ES2023
  return [...(items ?? [])].sort(
    (a, b) => TITLE_ORDER.indexOf(a.kind) - TITLE_ORDER.indexOf(b.kind),
  )[0]
}
