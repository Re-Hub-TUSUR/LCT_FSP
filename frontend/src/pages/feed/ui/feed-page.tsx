import { useState } from 'react'
import type { CandidateMatchDto } from '@/entities/candidate'
import { useSession } from '@/entities/session'
import type { VacancyMatchDto } from '@/entities/vacancy'
import { Page } from '@/shared/ui'
import { CandidateFeed, CandidatePanel } from '@/widgets/candidate-feed'
import { CandidateSwipe, DecisionCounters, FeedViewTabs, VacancySwipe } from '@/widgets/feed-swipe'
import { VacancyFeed, VacancyPanel } from '@/widgets/vacancy-feed'

export function FeedPage() {
  const { user } = useSession()
  const employer = user?.role === 'employer'

  return (
    <Page
      title={employer ? 'Кандидаты' : 'Вакансии для вас'}
      lead={
        employer
          ? 'Банк категоризированных кандидатов: поиск, фильтры и объяснимый рейтинг'
          : 'Только подходящие вам вакансии — по категории, стеку и предпочтениям'
      }
      actions={<FeedViewTabs role={employer ? 'employer' : 'candidate'} />}
    >
      {employer ? <CandidateFeed /> : <VacancyFeed />}
    </Page>
  )
}

export function FeedSwipePage() {
  const { user } = useSession()
  const employer = user?.role === 'employer'
  const [vacancy, setVacancy] = useState<VacancyMatchDto | null>(null)
  const [profileStack, setProfileStack] = useState<readonly string[]>([])
  const [candidate, setCandidate] = useState<CandidateMatchDto | null>(null)

  return (
    <Page
      className="page--swipe"
      title={employer ? 'Подбор свайпами' : 'Вакансии свайпами'}
      lead="Вправо — интересно, влево — пропустить. Клавиши ← и → тоже работают"
      actions={<DecisionCounters role={employer ? 'employer' : 'candidate'} />}
    >
      {employer ? (
        <CandidateSwipe onStudy={setCandidate} />
      ) : (
        <VacancySwipe
          onStudy={(match, stack) => {
            setVacancy(match)
            setProfileStack(stack)
          }}
        />
      )}
      {vacancy && (
        <VacancyPanel
          match={vacancy}
          profileStack={profileStack}
          onClose={() => setVacancy(null)}
        />
      )}
      {candidate && <CandidatePanel match={candidate} onClose={() => setCandidate(null)} />}
    </Page>
  )
}
