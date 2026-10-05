import { useSearchParams } from 'react-router'
import { Page } from '@/shared/ui'
import { CandidateDeck } from '@/widgets/candidate-deck'

export function MatchingSwipePage() {
  const [params] = useSearchParams()

  // TODO(matching): "describe the need" form (stack, specialization, grade) that produces needId.
  return (
    <Page
      title="Подбор"
      lead="Кандидаты из подходящих категорий, ранжированные по подтверждённому профилю"
    >
      <CandidateDeck needId={params.get('need') ?? undefined} />
    </Page>
  )
}
