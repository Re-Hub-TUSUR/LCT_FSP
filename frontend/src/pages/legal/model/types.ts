/** A table cell: one paragraph, or several; a paragraph starting with «- » is a list item. */
export type LegalCell = string | string[]

export type LegalBlock =
  | { t: 'h1'; text: string }
  | { t: 'h2'; text: string }
  | { t: 'p'; text: string }
  /** A numbered clause: «1.1.» and its text. */
  | { t: 'c'; num: string; text: string }
  /** Items labelled а), б), в) … */
  | { t: 'subs'; items: string[] }
  | { t: 'bullets'; items: string[] }
  | { t: 'table'; header: boolean; widths: number[]; rows: LegalCell[][] }
  /** A heading with a two-column «label | value» table. */
  | { t: 'card'; title: string; rows: [string, LegalCell][] }
  | { t: 'callout'; title: string; lines: string[] }
  /** A page break of the Word version; nothing on the web. */
  | { t: 'break' }

/**
 * Inline markup in every text: `**bold**` and `~~italic~~`. The text comes from the Word
 * versions in `public/legal`, which are the source of truth.
 */
export type LegalDocument = {
  title: string
  subtitle: string
  meta: [string, string][]
  /** Titles of the top-level sections, in order. */
  toc: string[]
  blocks: LegalBlock[]
}
