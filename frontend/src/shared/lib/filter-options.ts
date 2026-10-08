/** Helpers of the filter panels: suggestions for typed terms and comparing chosen values. */

export type CountedTerm = { value: string; count: number }

export type TermOption = { value: string; label: string; count: number; hint?: string }

const MAX_TERM_OPTIONS = 8

/** «Node.js» and «nodejs», «ё» and «е» compare equal. */
export function squashTerm(text: string): string {
  return text.toLowerCase().replace(/ё/g, 'е').replace(/[\s-]/g, '')
}

/**
 * Known terms for a typed text, the chosen ones left out: names containing it, then IT slang
 * («питон» → Python, with a hint). Prefix matches first, then the most frequent.
 */
export function termOptions(
  known: readonly CountedTerm[],
  query: string,
  chosen: readonly string[],
  synonyms: readonly (readonly string[])[] = [],
): TermOption[] {
  const taken = new Set(chosen.map(squashTerm))
  const needle = squashTerm(query)
  const ranked: (TermOption & { rank: number })[] = []
  const seen = new Set<string>()
  for (const item of known) {
    const key = squashTerm(item.value)
    if (taken.has(key) || !key.includes(needle)) continue
    seen.add(key)
    ranked.push({ ...item, label: item.value, rank: key.startsWith(needle) ? 0 : 1 })
  }
  if (needle) {
    for (const group of synonyms) {
      const word = group.find((member) => squashTerm(member).startsWith(needle))
      if (!word) continue
      const members = new Set(group.map(squashTerm))
      for (const item of known) {
        const key = squashTerm(item.value)
        if (!members.has(key) || seen.has(key) || taken.has(key)) continue
        seen.add(key)
        ranked.push({ ...item, label: item.value, hint: `по запросу «${word}»`, rank: 0 })
      }
    }
  }
  // oxlint-disable-next-line unicorn/no-array-sort -- a fresh array; toSorted() needs ES2023
  const sorted = ranked.sort((a, b) => a.rank - b.rank || b.count - a.count)
  return sorted.slice(0, MAX_TERM_OPTIONS).map(({ rank: _rank, ...option }) => option)
}

/** The known term a typed word stands for: the same name or IT slang for it. */
export function resolveTerm(
  known: readonly CountedTerm[],
  text: string,
  synonyms: readonly (readonly string[])[] = [],
): string | null {
  const needle = squashTerm(text)
  if (!needle) return null
  const same = known.find((item) => squashTerm(item.value) === needle)
  if (same) return same.value
  const group = synonyms.find((members) => members.some((word) => squashTerm(word) === needle))
  if (!group) return null
  const members = new Set(group.map(squashTerm))
  return known.find((item) => members.has(squashTerm(item.value)))?.value ?? null
}

/** The same values in any order. */
export function sameItems(a: readonly unknown[], b: readonly unknown[]): boolean {
  const left = new Set(a)
  const right = new Set(b)
  return left.size === right.size && [...left].every((item) => right.has(item))
}

/** `values` with `value` added once or removed. */
export function toggled<T>(values: readonly T[], value: T): T[] {
  return values.includes(value) ? values.filter((item) => item !== value) : [...values, value]
}
