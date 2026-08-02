import { useAuthStore } from '../../auth/store/authStore'
import { API_BASE_URL } from '../../../shared/config/env'
import { apiRequest } from '../../../shared/api/apiClient'
import {
  type CoachConversationMessages,
  type CoachStreamEvent,
} from '../types'
import { type CoachPageContext } from '../services/coachContext'

export function getActiveCoachConversation(pageContext: CoachPageContext) {
  const query = new URLSearchParams({
    page_type: pageContext.page_type,
  })
  if (pageContext.context_id) {
    query.set('context_id', pageContext.context_id)
  }

  return apiRequest<CoachConversationMessages | undefined>(
    `/coach/conversations/active/?${query.toString()}`,
  )
}

export async function streamCoachTurn({
  conversationId,
  pageContext,
  message,
  onEvent,
}: {
  conversationId: string | null
  pageContext: CoachPageContext
  message: string
  onEvent: (event: CoachStreamEvent) => void
}) {
  const token = useAuthStore.getState().accessToken
  const response = await fetch(`${API_BASE_URL}/coach/turns/stream/`, {
    method: 'POST',
    credentials: 'include',
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      Accept: 'text/event-stream',
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      conversation_id: conversationId ?? undefined,
      page_context: pageContext,
      message,
    }),
  })

  if (!response.ok || !response.body) {
    throw new Error(`Coach request failed with status ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { value, done } = await reader.read()
    if (done) {
      break
    }
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      const event = parseSseEvent(chunk)
      if (event) {
        onEvent(event)
      }
    }
  }

  const finalEvent = parseSseEvent(buffer)
  if (finalEvent) {
    onEvent(finalEvent)
  }
}

function parseSseEvent(chunk: string): CoachStreamEvent | null {
  const eventLine = chunk
    .split('\n')
    .find((line) => line.startsWith('event: '))
  const dataLine = chunk
    .split('\n')
    .find((line) => line.startsWith('data: '))

  if (!eventLine || !dataLine) {
    return null
  }

  return {
    event: eventLine.slice('event: '.length),
    data: JSON.parse(dataLine.slice('data: '.length)),
  } as CoachStreamEvent
}
