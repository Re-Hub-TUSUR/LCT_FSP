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

/** An eye, crossed out while the card is in the feed: «Скрыть», as on hh.ru. */
function EyeIcon({ crossed }: { crossed: boolean }) {
  return (
    <svg viewBox="0 0 24 24" width="18" height="18" aria-hidden="true" focusable="false">
      <path d="M2 12s3.6-7 10-7 10 7 10 7-3.6 7-10 7S2 12 2 12Z" />
      <circle cx="12" cy="12" r="3" />
      {crossed && <path d="M4 4l16 16" />}
    </svg>
  )
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
  const hidden = reaction === 'skip'

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
      {/* «Не интересно» is an icon in the corner of the card; a hidden card shows an open eye
          that brings it back. */}
      <button
        type="button"
        aria-pressed={hidden}
        aria-label={hidden ? 'Вернуть в ленту' : 'Скрыть'}
        title={hidden ? 'Вернуть в ленту' : 'Скрыть — не интересно'}
        className={hidden ? 'reaction-hide is-on' : 'reaction-hide'}
        onClick={() => toggle('skip')}
      >
        <EyeIcon crossed={!hidden} />
      </button>
    </div>
  )
}
