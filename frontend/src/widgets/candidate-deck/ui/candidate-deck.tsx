import { useState } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Link } from 'react-router'
import { CandidateCard } from '@/entities/candidate'
import { matchQueries } from '@/entities/match'
import { InviteCandidateForm } from '@/features/invite-candidate'
import { paths } from '@/shared/config'
import { Button, EmptyState, QueryState } from '@/shared/ui'
import { useSwipe } from '../lib/use-swipe'
import './candidate-deck.css'

/**
 * Employer-side matching: the employer, not the candidate, takes the initiative (LHH-style).
 * Swipe left (or "Пропустить") — skip, swipe right (or "Пригласить") — open the invitation form.
 * TODO(matching): persist skip decisions on the backend so the deck does not repeat candidates.
 */
export function CandidateDeck({ needId }: { needId?: string }) {
  const query = useQuery(matchQueries.recommendations(needId))
  const [index, setIndex] = useState(0)
  const [inviting, setInviting] = useState(false)

  const skip = () => {
    setInviting(false)
    setIndex((i) => i + 1)
  }
  const invite = () => setInviting(true)
  // Swipe is a pointer shortcut; the buttons below are the keyboard / screen reader path.
  const swipe = useSwipe({ onSwipeLeft: skip, onSwipeRight: invite })

  return (
    <QueryState
      query={query}
      isEmpty={(data) => data.items.length === 0}
      emptyTitle="Подходящих кандидатов пока нет"
    >
      {(data) => {
        const current = data.items[index]
        if (!current) {
          return (
            <EmptyState title="Вы просмотрели всю подборку">
              Уточните потребность, чтобы получить новых кандидатов.
            </EmptyState>
          )
        }
        const { candidate, reasons, score } = current

        return (
          <div className="deck">
            <p className="deck__counter" aria-live="polite">
              {index + 1} из {data.items.length}
            </p>
            <div
              className="deck__card"
              style={{
                transform: `translateX(${swipe.offset}px) rotate(${swipe.offset / 30}deg)`,
              }}
              {...swipe.bind}
            >
              <CandidateCard
                candidate={candidate}
                actions={
                  <Link to={paths.matchingProfile('candidate', candidate.id)}>Открыть профиль</Link>
                }
              />
              <section className="deck__reasons" aria-label="Почему кандидат в подборке">
                <p className="deck__score">Соответствие: {Math.round(score * 100)}%</p>
                <ul>
                  {reasons.map((reason) => (
                    <li key={reason}>{reason}</li>
                  ))}
                </ul>
              </section>
            </div>

            <div className="deck__controls">
              <Button variant="ghost" size="inline" onClick={skip}>
                Пропустить
              </Button>
              <Button size="inline" onClick={invite}>
                Пригласить
              </Button>
            </div>

            {inviting && <InviteCandidateForm candidateId={candidate.id} onSent={skip} />}
          </div>
        )
      }}
    </QueryState>
  )
}
