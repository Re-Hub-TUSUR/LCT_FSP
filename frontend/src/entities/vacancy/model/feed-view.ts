import type { FeedView } from '../api/vacancy-api'

/** Lists of the user's own decisions. Named after the cutting room, like the swipe reel. */
export type DecisionView = 'liked' | 'matched' | 'skipped'

export const DECISION_VIEWS: readonly DecisionView[] = ['liked', 'matched', 'skipped']

export const DECISION_VIEW_LABELS: Record<DecisionView, string> = {
  /** Liked. */
  liked: 'Отобрано',
  /** Liked, and the other side liked back. */
  matched: 'Взаимно',
  /** Skipped; a card can be taken back from here. */
  skipped: 'Не интересно',
}

/** A feed page shows everything or one of the decision lists (`unseen` is the swipe deck's). */
export type ListView = 'all' | DecisionView

/** The `view` of a feed URL; anything unknown is the main list. */
export function parseListView(value: string | null): ListView {
  return DECISION_VIEWS.includes(value as DecisionView) ? (value as DecisionView) : 'all'
}

export type { FeedView }
