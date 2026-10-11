import { useSearchParams } from 'react-router'
import type { CandidateMatchDto } from '@/entities/candidate'
import { InviteCandidateLink } from '@/features/invite-candidate'
import { HackerRain, Page } from '@/shared/ui'
import { CandidateList } from '@/widgets/candidate-feed'
import { Messenger } from '@/widgets/messenger'
import { ResponsesHub } from '@/widgets/responses-hub'
import { VacancyList } from '@/widgets/vacancy-feed'
import './responses-page.css'

/** «Мне понравились»: the next step with a liked candidate is the invitation. */
function inviteLink(match: CandidateMatchDto) {
  return <InviteCandidateLink candidateId={match.candidate.id} />
}

export function ResponsesPage() {
  const [params, setParams] = useSearchParams()
  const chatId = params.get('chat')

  return (
    <Page
      className="page--responses"
      title="Мои отклики"
      lead="Пропуски, избранное, входящие симпатии и переписка после взаимного интереса"
    >
      <HackerRain />
      <ResponsesHub
        renderCandidates={(items, tab) => (
          <CandidateList
            items={items}
            view={tab}
            rowExtra={tab === 'liked' ? inviteLink : undefined}
          />
        )}
        renderVacancies={(items, profileStack) => (
          <VacancyList items={items} profileStack={profileStack} />
        )}
        messagesPanel={
          <Messenger
            selectedId={chatId}
            onSelect={(id) => setParams({ tab: 'messages', chat: id })}
          />
        }
      />
    </Page>
  )
}
