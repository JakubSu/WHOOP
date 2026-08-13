import { useAuthStore } from '../../auth/store/authStore'
import { API_BASE_URL } from '../../../shared/config/env'
import { apiRequest } from '../../../shared/api/apiClient'
import {
  type CoachConversation,
  type CoachConversationPage,
  type CoachMessagePage,
  type CoachStreamEvent,
} from '../types'

export function createCoachConversation() {
  return coachRequest<CoachConversation>('/coach/conversations', {
    method: 'POST',
  })
}

export function listCoachConversations(cursor?: string) {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''
  return coachRequest<CoachConversationPage>(`/coach/conversations${query}`)
}

export function getCoachMessages(conversationId: string, cursor?: string) {
  const query = cursor ? `?cursor=${encodeURIComponent(cursor)}` : ''
  return coachRequest<CoachMessagePage>(
    `/coach/conversations/${conversationId}/messages${query}`,
  )
}

export function renameCoachConversation(conversationId: string, title: string) {
  return coachRequest<CoachConversation>(`/coach/conversations/${conversationId}`, {
    method: 'PATCH',
    body: JSON.stringify({ title }),
  })
}

export function deleteCoachConversation(conversationId: string) {
  return coachRequest<void>(`/coach/conversations/${conversationId}`, {
    method: 'DELETE',
  })
}

export async function streamCoachMessage({
  conversationId,
  content,
  onEvent,
}: {
  conversationId: string
  content: string
  onEvent: (event: CoachStreamEvent) => void
}) {
  const token = useAuthStore.getState().accessToken
  const response = await fetch(
    `${API_BASE_URL}/coach/conversations/${conversationId}/messages/stream`,
    {
      method: 'POST',
      credentials: 'include',
      headers: {
        ...(token ? { Authorization: `Bearer ${token}` } : {}),
        Accept: 'text/event-stream',
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ content }),
    },
  )

  if (!response.ok || !response.body) {
    throw new Error(`Coach request failed with status ${response.status}`)
  }

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''
  while (true) {
    const { value, done } = await reader.read()
    if (done) break
    buffer += decoder.decode(value, { stream: true })
    const chunks = buffer.split('\n\n')
    buffer = chunks.pop() ?? ''
    for (const chunk of chunks) {
      const event = parseSseEvent(chunk)
      if (event) onEvent(event)
    }
  }
  const finalEvent = parseSseEvent(buffer)
  if (finalEvent) onEvent(finalEvent)
}

function coachRequest<T>(path: string, init: RequestInit = {}) {
  const token = useAuthStore.getState().accessToken
  return apiRequest<T>(path, {
    ...init,
    headers: {
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...(init.body ? { 'Content-Type': 'application/json' } : {}),
      ...init.headers,
    },
    baseUrl: API_BASE_URL,
  })
}

function parseSseEvent(chunk: string): CoachStreamEvent | null {
  if (!chunk || chunk.startsWith(':')) return null
  const lines = chunk.split('\n')
  const eventLine = lines.find((line) => line.startsWith('event: '))
  const dataLine = lines.find((line) => line.startsWith('data: '))
  if (!eventLine || !dataLine) return null
  return {
    event: eventLine.slice('event: '.length),
    data: JSON.parse(dataLine.slice('data: '.length)),
  } as CoachStreamEvent
}
