import { useSearchParams } from 'react-router'
import { HackerRain, Page } from '@/shared/ui'
import { Messenger } from '@/widgets/messenger'
import { ResponsesHub } from '@/widgets/responses-hub'
import './responses-page.css'

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
