import { API_BASE_URL } from '../../../shared/config/env'
import { apiFetch, apiRequest } from '../../../shared/api/apiClient'
import {
  type CoachConversation,
  type CoachConversationPage,
  type CoachMessagePage,
  type CoachStreamEvent,
  type CoachMessage,
} from '../types'
import { type CoachViewContext } from '../services/coachContext'

export function createCoachConversation() {
  return coachRequest<CoachConversation>('/coach/conversations', {
    method: 'POST',
  })
}

export function dismissCoachUiAction(conversationId: string, actionId: string) {
  return coachRequest<CoachMessage>(`/coach/conversations/${conversationId}/ui-actions/${actionId}/dismiss`, { method: 'POST' })
}

export function resolveCoachUiAction({ conversationId, actionId, exerciseId, method, onEvent }: { conversationId: string; actionId: string; exerciseId: string; method: 'created' | 'selected'; onEvent: (event: CoachStreamEvent) => void }) {
  return streamCoachRequest(`/coach/conversations/${conversationId}/ui-actions/${actionId}/resolve/stream`, { exercise_id: exerciseId, method }, onEvent)
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
  viewContext,
  onEvent,
}: {
  conversationId: string
  content: string
  viewContext: CoachViewContext | null
  onEvent: (event: CoachStreamEvent) => void
}) {
  return streamCoachRequest(
    `/coach/conversations/${conversationId}/messages/stream`,
    viewContext ? { content, view_context: viewContext } : { content },
    onEvent,
  )
}

async function streamCoachRequest(path: string, body: object, onEvent: (event: CoachStreamEvent) => void) {
  const response = await apiFetch(path, {
    method: 'POST',
    headers: {
      Accept: 'text/event-stream',
    },
    body: JSON.stringify(body),
    baseUrl: API_BASE_URL,
  })

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
  return apiRequest<T>(path, {
    ...init,
    headers: {
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
