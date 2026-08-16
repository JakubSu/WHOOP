import {
  type CoachMessage,
  type CoachRecommendationTransition,
  type CoachStreamEvent,
} from '../types'

export type CoachChatState = {
  messages: CoachMessage[]
  activeMessageId: string | null
  thinking: boolean
}

export function applyCoachStreamEvent(
  state: CoachChatState,
  streamEvent: CoachStreamEvent,
): CoachChatState {
  const { event, data } = streamEvent
  if (event === 'message_started') {
    const message: CoachMessage = {
      id: data.message_id,
      role: 'assistant',
      content: '',
      created_at: new Date().toISOString(),
      activities: [],
      recommendation: null,
      ui_actions: [],
      operations: [],
    }
    return {
      messages: [...state.messages, message],
      activeMessageId: data.message_id,
      thinking: false,
    }
  }
  if (event === 'thinking_started') {
    return { ...state, thinking: true }
  }
  if (event === 'thinking_finished') {
    return { ...state, thinking: false }
  }
  if (event === 'text_delta') {
    return {
      ...state,
      thinking: false,
      messages: updateMessage(state.messages, data.message_id, (message) => ({
        ...message,
        content: `${message.content}${data.delta}`,
      })),
    }
  }
  if (
    event === 'tool_started' ||
    event === 'tool_completed' ||
    event === 'tool_failed'
  ) {
    return {
      ...state,
      thinking: false,
      messages: updateMessage(state.messages, data.message_id, (message) => ({
        ...message,
        activities: upsertById(message.activities, data.activity),
      })),
    }
  }
  if (event === 'completed') {
    return {
      messages: applyRecommendationTransitions(
        replaceMessages(
          updateMessage(state.messages, data.message_id, () => data.message),
          data.updated_messages ?? [],
        ),
        data.recommendation_transitions ?? [],
      ),
      activeMessageId: null,
      thinking: false,
    }
  }
  if (event === 'error') {
    return { ...state, activeMessageId: null, thinking: false }
  }
  return state
}

function replaceMessages(messages: CoachMessage[], replacements: CoachMessage[]) {
  const byId = new Map(replacements.map((message) => [message.id, message]))
  return messages.map((message) => byId.get(message.id) ?? message)
}

function updateMessage(
  messages: CoachMessage[],
  messageId: string,
  update: (message: CoachMessage) => CoachMessage,
) {
  return messages.map((message) =>
    message.id === messageId ? update(message) : message,
  )
}

function applyRecommendationTransitions(
  messages: CoachMessage[],
  transitions: CoachRecommendationTransition[],
) {
  return messages.map((message) => {
    const transition = transitions.find(
      (item) => item.recommendation_id === message.recommendation?.id,
    )
    if (!transition || !message.recommendation) return message
    return {
      ...message,
      recommendation: {
        ...message.recommendation,
        status: transition.status,
        actionable: false,
      },
    }
  })
}

function upsertById<T extends { id: string }>(items: T[], item: T): T[] {
  const index = items.findIndex((candidate) => candidate.id === item.id)
  return index === -1
    ? [...items, item]
    : items.map((candidate, candidateIndex) => index === candidateIndex ? item : candidate)
}
