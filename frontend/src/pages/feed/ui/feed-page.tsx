import { Link, useLocation } from 'react-router'
import { useSession } from '@/entities/session'
import { ROUTES } from '@/shared/config'
import { Page } from '@/shared/ui'
import { CandidateFeed } from '@/widgets/candidate-feed'
import { CandidateSwipe, VacancySwipe } from '@/widgets/feed-swipe'
import { VacancyFeed } from '@/widgets/vacancy-feed'
import './feed-page.css'

/** «Лента ⇄ Свайпы»: two pages over the same ranking, switched by one button. */
function ModeSwitch({ mode }: { mode: 'list' | 'swipe' }) {
  // Filters and the selected vacancy carry over between the two modes.
  const { search } = useLocation()
  return (
    <nav className="mode-switch" aria-label="Режим просмотра">
      <Link
        to={`${ROUTES.feed}${search}`}
        className={mode === 'list' ? 'is-active' : undefined}
        aria-current={mode === 'list' ? 'page' : undefined}
      >
        Лента
      </Link>
      <Link
        to={`${ROUTES.feedSwipe}${search}`}
        className={mode === 'swipe' ? 'is-active' : undefined}
        aria-current={mode === 'swipe' ? 'page' : undefined}
      >
        Свайпы
      </Link>
    </nav>
  )
}

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
      actions={<ModeSwitch mode="list" />}
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
      title={employer ? 'Подбор свайпами' : 'Вакансии свайпами'}
      lead="Вправо — интересно, влево — пропустить. Клавиши ← и → тоже работают"
      actions={<ModeSwitch mode="swipe" />}
    >
      {employer ? <CandidateSwipe /> : <VacancySwipe />}
    </Page>
  )
}
