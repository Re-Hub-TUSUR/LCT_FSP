import { useSession } from '@/entities/session'
import { Page } from '@/shared/ui'
import { CandidateFeed } from '@/widgets/candidate-feed'
import { CandidateSwipe, DecisionCounters, VacancySwipe } from '@/widgets/feed-swipe'
import { VacancyFeed } from '@/widgets/vacancy-feed'

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
    >
      {employer ? <CandidateFeed /> : <VacancyFeed />}
    </Page>
  )
}

export function FeedSwipePage() {
  const { user } = useSession()
  const employer = user?.role === 'employer'

  return (
    <Page
      className="page--swipe"
      title={employer ? 'Подбор свайпами' : 'Вакансии свайпами'}
      lead="Вправо — интересно, влево — пропустить. Клавиши ← и → тоже работают"
      actions={<DecisionCounters role={employer ? 'employer' : 'candidate'} />}
    >
      {employer ? <CandidateSwipe /> : <VacancySwipe />}
    </Page>
  )
}
