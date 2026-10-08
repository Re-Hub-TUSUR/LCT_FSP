import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import type { UseQueryResult } from '@tanstack/react-query'
import { useSearchParams } from 'react-router'
import { CandidateMatchCard, candidateQueries } from '@/entities/candidate'
import type { CandidateMatchDto } from '@/entities/candidate'
import { VacancyMatchCard, vacancyQueries } from '@/entities/vacancy'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { useLikeVacancy, useReaction } from '@/features/feed-reaction'
import type { Paginated } from '@/shared/api'
import { EmptyState, FeedSkeleton, QueryState, SwipeDeck } from '@/shared/ui'
import type { SwipeDecision } from '@/shared/ui'

const BATCH = 10
// Ask for the next cards before the queue runs out.
const REFILL_AT = 3

/**
 * The deck shows the fetched cards minus the ones decided in this session. The server hides
 * decided cards (`view=unseen`), so a refetch brings the next ones.
 */
function useQueue<T>(
  query: UseQueryResult<Paginated<T>>,
  keyOf: (item: T) => string,
): { queue: T[]; pop: (item: T) => void; restore: (item: T) => void } {
  const [decided, setDecided] = useState<ReadonlySet<string>>(() => new Set())
  const queue = (query.data?.items ?? []).filter((item) => !decided.has(keyOf(item)))
  const left = (query.data?.total ?? 0) - decided.size
  const { refetch, isFetching } = query

  useEffect(() => {
    if (!isFetching && queue.length < REFILL_AT && left > queue.length) void refetch()
  }, [isFetching, queue.length, left, refetch])

  const pop = (item: T) => setDecided((previous) => new Set(previous).add(keyOf(item)))
  /** The decision was taken back: the card returns to the deck. */
  const restore = (item: T) =>
    setDecided((previous) => {
      const next = new Set(previous)
      next.delete(keyOf(item))
      return next
    })
  return { queue, pop, restore }
}

const vacancyKey = (match: VacancyMatchDto) => match.vacancy.id
const candidateKey = (match: CandidateMatchDto) => match.candidate.id

export function VacancySwipe({
  onStudy,
}: {
  onStudy?: (match: VacancyMatchDto, profileStack: readonly string[]) => void
}) {
  const query = useQuery(vacancyQueries.feed({ page: 1, perPage: BATCH, view: 'unseen' }))
  const { queue, pop } = useQueue(query, vacancyKey)
  const reaction = useReaction()
  const stack = query.data?.basis?.stack ?? []

  const decide = (match: VacancyMatchDto, decision: SwipeDecision) => {
    pop(match)
    reaction.mutate({ target: 'vacancy', id: match.vacancy.id, kind: decision })
  }

  if (query.isPending) return <FeedSkeleton count={1} />
  if (query.isError) return <QueryState query={query}>{() => null}</QueryState>
  return (
    <SwipeDeck
      items={queue}
      getKey={vacancyKey}
      renderCard={(match) => (
        <VacancyMatchCard
          match={match}
          frame
          onStudy={onStudy ? () => onStudy(match, stack) : undefined}
        />
      )}
      onDecide={decide}
      likeLabel="Интересно"
      skipLabel="Пропустить"
      empty={
        <EmptyState title="Вы посмотрели все подходящие вакансии">
          Отобранные — в ленте, раздел «Отобрано». Новые появятся здесь сами.
        </EmptyState>
      }
    />
  )
}

/** Recruiter's deck; with `?vacancyId=` the cards are ranked by fit to that vacancy. */
export function CandidateSwipe({ onStudy }: { onStudy?: (match: CandidateMatchDto) => void }) {
  const [params] = useSearchParams()
  const vacancyId = params.get('vacancyId') ?? undefined
  const query = useQuery(
    candidateQueries.search({ page: 1, perPage: BATCH, view: 'unseen', vacancyId }),
  )
  const { queue, pop, restore } = useQueue(query, candidateKey)
  const reaction = useReaction()
  const likeVacancy = useLikeVacancy()

  const decide = (match: CandidateMatchDto, decision: SwipeDecision) => {
    pop(match)
    const send = (forVacancy: string | undefined) =>
      reaction.mutate({
        target: 'candidate',
        id: match.candidate.id,
        kind: decision,
        vacancyId: forVacancy,
      })
    // A like names the vacancy it is for; closing the choice takes the swipe back.
    if (decision === 'like' && !vacancyId) return likeVacancy.ask(send, () => restore(match))
    send(vacancyId)
  }

  if (query.isPending) return <FeedSkeleton count={1} />
  if (query.isError) return <QueryState query={query}>{() => null}</QueryState>
  return (
    <>
      {likeVacancy.dialog}
      <CandidateDeckView queue={queue} decide={decide} onStudy={onStudy} />
    </>
  )
}

function CandidateDeckView({
  queue,
  decide,
  onStudy,
}: {
  queue: CandidateMatchDto[]
  decide: (match: CandidateMatchDto, decision: SwipeDecision) => void
  onStudy?: (match: CandidateMatchDto) => void
}) {
  return (
    <SwipeDeck
      items={queue}
      getKey={candidateKey}
      renderCard={(match) => (
        <CandidateMatchCard
          match={match}
          frame
          onStudy={onStudy ? () => onStudy(match) : undefined}
        />
      )}
      onDecide={decide}
      likeLabel="Интересно"
      skipLabel="Пропустить"
      empty={
        <EmptyState title="Подборка закончилась">
          Отобранные кандидаты — в ленте, раздел «Отобрано».
        </EmptyState>
      }
    />
  )
}
