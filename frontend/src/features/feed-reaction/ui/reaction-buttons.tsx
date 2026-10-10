import { useState } from 'react'
import { useMutation, useQueryClient } from '@tanstack/react-query'
import { candidateApi, candidateKeys } from '@/entities/candidate'
import { vacancyApi, vacancyKeys } from '@/entities/vacancy'
import type { Reaction } from '@/entities/vacancy'
import { useLikeVacancy } from './vacancy-choice'
import './reaction-buttons.css'

export type ReactionTarget = 'vacancy' | 'candidate'

type Change = { target: ReactionTarget; id: string; kind: Reaction | null; vacancyId?: string }

function send({ target, id, kind, vacancyId }: Change) {
  if (target === 'vacancy') {
    return kind ? vacancyApi.react(id, kind) : vacancyApi.clearReaction(id)
  }
  return kind ? candidateApi.react(id, kind, vacancyId) : candidateApi.clearReaction(id)
}

/** Saves a like / skip. The card updates at once; lists refresh when the server confirms. */
export function useReaction() {
  const queryClient = useQueryClient()
  return useMutation({
    mutationFn: send,
    onSuccess: (_, change) => {
      const key = change.target === 'vacancy' ? vacancyKeys.all : candidateKeys.all
      void queryClient.invalidateQueries({ queryKey: key })
    },
  })
}

type Props = {
  target: ReactionTarget
  id: string
  initial: Reaction | null
  vacancyId?: string
  likeLabel?: string
}

export function ReactionButtons({ target, id, initial, vacancyId, likeLabel = 'Отобрать' }: Props) {
  const [reaction, setReaction] = useState<Reaction | null>(initial)
  // The same candidate has buttons in the row and in the side sheet: a decision made in one
  // comes back to the other with the refreshed list.
  const [known, setKnown] = useState<Reaction | null>(initial)
  if (initial !== known) {
    setKnown(initial)
    setReaction(initial)
  }
  const mutation = useReaction()
  const likeVacancy = useLikeVacancy()
  const applicant = target === 'vacancy'

  const save = (next: Reaction | null, forVacancy = vacancyId) => {
    setReaction(next)
    mutation.mutate({ target, id, kind: next, vacancyId: forVacancy })
  }

  const toggle = (kind: Reaction) => {
    const next = reaction === kind ? null : kind
    // A recruiter's like names the vacancy it is for, unless the feed is open for one already.
    if (target === 'candidate' && next === 'like' && !vacancyId) {
      return likeVacancy.ask((chosen) => save(next, chosen))
    }
    save(next)
  }

  return (
    <div className="reaction-buttons">
      {likeVacancy.dialog}
      <button
        type="button"
        aria-pressed={reaction === 'like'}
        className={`reaction-buttons__btn reaction-buttons__btn--like${reaction === 'like' ? ' is-on' : ''}`}
        onClick={() => toggle('like')}
      >
        {applicant
          ? reaction === 'like'
            ? '✓ Вы откликнулись'
            : 'Откликнуться'
          : reaction === 'like'
            ? '★ Отобрано'
            : `☆ ${likeLabel}`}
      </button>
      {/* A candidate answers a vacancy with one button; a skipped one (from the swipes) can be
          brought back. */}
      {(!applicant || reaction === 'skip') && (
        <button
          type="button"
          aria-pressed={reaction === 'skip'}
          className={`reaction-buttons__btn${reaction === 'skip' ? ' is-on' : ''}`}
          onClick={() => toggle('skip')}
        >
          {reaction === 'skip' ? 'Вырезано · вернуть' : 'Не интересно'}
        </button>
      )}
    </div>
  )
}
