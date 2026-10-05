import { useEffect, useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { CandidateMatchCard, candidateQueries, demoCandidateSearch } from '@/entities/candidate'
import type { CandidateMatchDto } from '@/entities/candidate'
import { demoVacancyFeed, VacancyMatchCard, vacancyQueries } from '@/entities/vacancy'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { useReaction } from '@/features/feed-reaction'
import { ApiError } from '@/shared/api'
import { EmptyState, FeedSkeleton, Notice, SwipeDeck } from '@/shared/ui'
import type { SwipeDecision } from '@/shared/ui'

const BATCH = 10
// Ask for the next cards before the queue runs out.
const REFILL_AT = 3

const isNotReady = (error: unknown) =>
  error instanceof ApiError && [0, 404, 501].includes(error.status)

/**
 * The deck shows the fetched cards minus the ones decided in this session. The server already
 * hides decided cards (`view=unseen`), so a refetch brings the next ones.
 */
function useQueue<T>(incoming: T[] | undefined, keyOf: (item: T) => string) {
  const [decided, setDecided] = useState<ReadonlySet<string>>(() => new Set())
  const queue = (incoming ?? []).filter((item) => !decided.has(keyOf(item)))
  const pop = (item: T) => setDecided((previous) => new Set(previous).add(keyOf(item)))
  return { queue, pop }
}

const vacancyKey = (match: VacancyMatchDto) => match.vacancy.id
const candidateKey = (match: CandidateMatchDto) => match.candidate.id

export function VacancySwipe() {
  const query = useQuery(vacancyQueries.feed({ page: 1, perPage: BATCH, view: 'unseen' }))
  const demo = query.isError && isNotReady(query.error)
  const items = query.data?.items ?? (demo ? demoVacancyFeed(1, BATCH).items : undefined)
  const { queue, pop } = useQueue(items, vacancyKey)
  const reaction = useReaction()

  useEffect(() => {
    if (!demo && query.data && queue.length < REFILL_AT && query.data.total > queue.length) {
      void query.refetch()
    }
  }, [demo, query, queue.length])

  const decide = (match: VacancyMatchDto, decision: SwipeDecision) => {
    pop(match)
    reaction.mutate({ target: 'vacancy', id: match.vacancy.id, kind: decision })
  }

  if (!items && query.isPending) return <FeedSkeleton count={1} />
  return (
    <>
      {demo && <Notice>Демо-данные: API ленты ещё в разработке</Notice>}
      <SwipeDeck
        items={queue}
        getKey={vacancyKey}
        renderCard={(match) => <VacancyMatchCard match={match} expanded />}
        onDecide={decide}
        likeLabel="Интересно"
        skipLabel="Пропустить"
        empty={
          <EmptyState title="Вы посмотрели все подходящие вакансии">
            Понравившиеся — в избранном ленты. Новые появятся здесь сами.
          </EmptyState>
        }
      />
    </>
  )
}

export function CandidateSwipe() {
  const query = useQuery(candidateQueries.search({ page: 1, perPage: BATCH, view: 'unseen' }))
  const demo = query.isError && isNotReady(query.error)
  const items = query.data?.items ?? (demo ? demoCandidateSearch(1, BATCH).items : undefined)
  const { queue, pop } = useQueue(items, candidateKey)
  const reaction = useReaction()

  useEffect(() => {
    if (!demo && query.data && queue.length < REFILL_AT && query.data.total > queue.length) {
      void query.refetch()
    }
  }, [demo, query, queue.length])

  const decide = (match: CandidateMatchDto, decision: SwipeDecision) => {
    pop(match)
    reaction.mutate({ target: 'candidate', id: match.candidate.id, kind: decision })
  }

  if (!items && query.isPending) return <FeedSkeleton count={1} />
  return (
    <>
      {demo && <Notice>Демо-данные: API поиска ещё в разработке</Notice>}
      <SwipeDeck
        items={queue}
        getKey={candidateKey}
        renderCard={(match) => <CandidateMatchCard match={match} />}
        onDecide={decide}
        likeLabel="В избранное"
        skipLabel="Пропустить"
        empty={
          <EmptyState title="Подборка закончилась">
            Избранные кандидаты — в ленте, вкладка «Избранное».
          </EmptyState>
        }
      />
    </>
  )
}
