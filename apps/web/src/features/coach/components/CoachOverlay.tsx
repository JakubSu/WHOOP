import { Bot, ChevronDown, Send, Sparkles } from 'lucide-react'
import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'
import { getActiveCoachConversation, streamCoachTurn } from '../api/coachApi'
import { useCoachOverlayContext } from '../context/CoachOverlayContext'
import {
  areCoachContextsEqual,
  labelForCoachContext,
  type CoachPageContext,
} from '../services/coachContext'
import {
  contextForNextSubmittedTurn,
  shouldSwitchConversationOnSend,
} from '../services/coachOverlayState'
import {
  type CoachChatItem,
  type CoachConversationMessages,
  type CoachStreamEvent,
} from '../types'
import { RecommendationPanel } from '../../recommendations/components/RecommendationPanel'
import {
  approveRecommendationOperation,
  normalizeRecommendation,
  rejectRecommendationOperation,
} from '../../recommendations/api/recommendationApi'
import { type Recommendation } from '../../recommendations/types'

type ConversationState = {
  conversationId: string | null
  context: CoachPageContext
  items: CoachChatItem[]
  hasLoaded: boolean
}

export function CoachOverlay() {
  const { currentContext } = useCoachOverlayContext()
  const [isOpen, setIsOpen] = useState(false)
  const [visibleConversation, setVisibleConversation] =
    useState<ConversationState | null>(null)
  const [input, setInput] = useState('')
  const [isLoadingConversation, setIsLoadingConversation] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [operationBusyId, setOperationBusyId] = useState<string | null>(null)

  const currentLabel = labelForCoachContext(currentContext)
  const visibleLabel = labelForCoachContext(visibleConversation?.context ?? null)
  const showContextShift =
    isOpen &&
    currentContext &&
    visibleConversation &&
    !areCoachContextsEqual(currentContext, visibleConversation.context)

  const loadConversation = useCallback(async (context: CoachPageContext) => {
    setIsLoadingConversation(true)
    try {
      const active = await getActiveCoachConversation(context)
      const nextState = active
        ? conversationFromActive(context, active)
        : {
            conversationId: null,
            context,
            items: [],
            hasLoaded: true,
          }
      setVisibleConversation(nextState)
      return nextState
    } finally {
      setIsLoadingConversation(false)
    }
  }, [])

  const openCoach = useCallback(async () => {
    if (!currentContext) {
      return
    }
    setIsOpen(true)
    if (
      !visibleConversation ||
      (!isStreaming &&
        !areCoachContextsEqual(visibleConversation.context, currentContext))
    ) {
      await loadConversation(currentContext)
    }
  }, [currentContext, isStreaming, loadConversation, visibleConversation])

  const launcherText = useMemo(() => {
    if (isStreaming) {
      return 'Coach is thinking'
    }
    return `Coach · ${currentLabel}`
  }, [currentLabel, isStreaming])

  useEffect(() => {
    if (!currentContext) {
      setIsOpen(false)
    }
  }, [currentContext])

  if (!currentContext && !isOpen) {
    return null
  }

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    const message = input.trim()
    if (!message || isStreaming) {
      return
    }
    const nextContext = contextForNextSubmittedTurn({
      visibleContext: visibleConversation?.context ?? null,
      currentContext,
    })
    if (!nextContext) {
      return
    }

    setInput('')
    setIsStreaming(true)

    try {
      let conversation = visibleConversation
      if (
        !conversation ||
        shouldSwitchConversationOnSend({
          visibleContext: conversation.context,
          currentContext: nextContext,
        })
      ) {
        conversation = await loadConversation(nextContext)
      }

      const userItem: CoachChatItem = {
        id: `local-user-${Date.now()}`,
        type: 'message',
        role: 'user',
        content: message,
      }
      setVisibleConversation((state) =>
        state
          ? {
              ...state,
              items: [...state.items, userItem],
            }
          : state,
      )

      await streamCoachTurn({
        conversationId: conversation.conversationId,
        pageContext: nextContext,
        message,
        onEvent: (streamEvent) => applyStreamEvent(streamEvent),
      })
    } catch (error) {
      const content =
        error instanceof Error
          ? error.message
          : 'I could not complete that coach turn.'
      setVisibleConversation((state) =>
        state
          ? {
              ...state,
              items: [
                ...state.items,
                {
                  id: `error-${Date.now()}`,
                  type: 'error',
                  content,
                },
              ],
            }
          : state,
      )
    } finally {
      setIsStreaming(false)
    }
  }

  function applyStreamEvent(streamEvent: CoachStreamEvent) {
    setVisibleConversation((state) => {
      if (!state) {
        return state
      }

      if (streamEvent.event === 'conversation_started') {
        return {
          ...state,
          conversationId: streamEvent.data.conversation_id,
          context: streamEvent.data.page_context,
        }
      }
      if (streamEvent.event === 'assistant_progress') {
        return appendItem(state, {
          id: `progress-${Date.now()}`,
          type: 'progress',
          content: streamEvent.data.message,
        })
      }
      if (streamEvent.event === 'tool_call_started') {
        return appendItem(state, {
          id: `tool-start-${Date.now()}`,
          type: 'tool',
          content: streamEvent.data.label ?? streamEvent.data.tool ?? 'Reading context',
        })
      }
      if (streamEvent.event === 'tool_call_completed') {
        return appendItem(state, {
          id: `tool-done-${Date.now()}`,
          type: 'tool',
          content: streamEvent.data.summary ?? 'Context ready',
        })
      }
      if (streamEvent.event === 'assistant_delta') {
        return appendAssistantDelta(state, streamEvent.data.text)
      }
      if (streamEvent.event === 'recommendation_created') {
        const recommendation = normalizeRecommendation(streamEvent.data.recommendation)
        return appendItem(state, {
          id: `recommendation-${recommendation.id}`,
          type: 'recommendation',
          recommendation,
        })
      }
      if (streamEvent.event === 'assistant_done') {
        return finishAssistantMessage(state, streamEvent.data.message.content)
      }
      if (streamEvent.event === 'error') {
        return appendItem(state, {
          id: `error-${Date.now()}`,
          type: 'error',
          content: streamEvent.data.message,
        })
      }

      return state
    })
  }

  async function handleOperation(
    recommendation: Recommendation,
    operationId: string,
    action: 'accept' | 'reject',
  ) {
    setOperationBusyId(operationId)
    try {
      const nextRecommendation =
        action === 'accept'
          ? await approveRecommendationOperation(recommendation.id, operationId)
          : await rejectRecommendationOperation(recommendation.id, operationId)
      setVisibleConversation((state) =>
        state ? replaceRecommendation(state, nextRecommendation) : state,
      )
    } finally {
      setOperationBusyId(null)
    }
  }

  return (
    <div className="coach-layer" aria-live={isStreaming ? 'polite' : 'off'}>
      {!isOpen ? (
        <button className="coach-launcher" type="button" onClick={openCoach}>
          <Sparkles aria-hidden="true" size={18} />
          <span>{launcherText}</span>
        </button>
      ) : (
        <section className="coach-panel" aria-label="AI coach chat">
          <header className="coach-panel__header">
            <div>
              <p className="coach-panel__eyebrow">Coach · {visibleLabel}</p>
              <h2>Ask about this training screen</h2>
            </div>
            <button
              className="coach-icon-button"
              type="button"
              aria-label="Collapse coach"
              onClick={() => setIsOpen(false)}
            >
              <ChevronDown aria-hidden="true" size={20} />
            </button>
          </header>

          <div className="coach-context-indicator">
            Current screen: {currentLabel}
            {showContextShift ? ' · next message switches context' : ''}
          </div>

          <div className="coach-messages">
            {isLoadingConversation ? (
              <p className="coach-empty-state">Loading this conversation...</p>
            ) : null}
            {!isLoadingConversation && !visibleConversation?.items.length ? (
              <div className="coach-empty-state">
                <Bot aria-hidden="true" size={22} />
                <p>Ask a question when you are ready.</p>
              </div>
            ) : null}
            {visibleConversation?.items.map((item) => {
              if (item.type === 'recommendation') {
                return (
                  <div className="coach-recommendation" key={item.id}>
                    <RecommendationPanel
                      recommendation={item.recommendation}
                      exerciseDisplays={[]}
                      onAcceptOperation={(operationId) =>
                        handleOperation(item.recommendation, operationId, 'accept')
                      }
                      onRejectOperation={(operationId) =>
                        handleOperation(item.recommendation, operationId, 'reject')
                      }
                      acceptingOperationId={operationBusyId}
                      rejectingOperationId={operationBusyId}
                    />
                  </div>
                )
              }

              return (
                <div
                  className={`coach-message coach-message--${item.type} ${
                    item.type === 'message' ? `coach-message--${item.role}` : ''
                  }`}
                  key={item.id}
                >
                  {item.content}
                </div>
              )
            })}
          </div>

          <form className="coach-compose" onSubmit={handleSubmit}>
            <input
              aria-label="Message coach"
              value={input}
              placeholder={isStreaming ? 'Coach is thinking...' : 'Message coach'}
              disabled={isStreaming || isLoadingConversation || !currentContext}
              onChange={(event) => setInput(event.target.value)}
            />
            <button
              className="coach-send-button"
              type="submit"
              aria-label="Send message"
              disabled={
                isStreaming ||
                isLoadingConversation ||
                !currentContext ||
                !input.trim()
              }
            >
              <Send aria-hidden="true" size={18} />
            </button>
          </form>
        </section>
      )}
    </div>
  )
}

function conversationFromActive(
  context: CoachPageContext,
  active: CoachConversationMessages,
): ConversationState {
  return {
    conversationId: active.conversation_id,
    context: active.page_context ?? context,
    hasLoaded: true,
    items: active.messages.map((message) => ({
      id: message.id,
      type: 'message',
      role: message.role,
      content: message.content,
    })),
  }
}

function appendItem(
  state: ConversationState,
  item: CoachChatItem,
): ConversationState {
  return {
    ...state,
    items: [...state.items, item],
  }
}

function appendAssistantDelta(
  state: ConversationState,
  text: string,
): ConversationState {
  const last = state.items[state.items.length - 1]
  if (
    last?.type === 'message' &&
    last.role === 'assistant' &&
    last.id === 'streaming-assistant'
  ) {
    return {
      ...state,
      items: [
        ...state.items.slice(0, -1),
        {
          ...last,
          content: `${last.content}${text}`,
        },
      ],
    }
  }

  return appendItem(state, {
    id: 'streaming-assistant',
    type: 'message',
    role: 'assistant',
    content: text,
  })
}

function finishAssistantMessage(
  state: ConversationState,
  content: string,
): ConversationState {
  const withoutStreaming = state.items.filter(
    (item) => item.id !== 'streaming-assistant',
  )
  return {
    ...state,
    items: [
      ...withoutStreaming,
      {
        id: `assistant-${Date.now()}`,
        type: 'message',
        role: 'assistant',
        content,
      },
    ],
  }
}

function replaceRecommendation(
  state: ConversationState,
  recommendation: Recommendation,
): ConversationState {
  return {
    ...state,
    items: state.items.map((item) =>
      item.type === 'recommendation' &&
      item.recommendation.id === recommendation.id
        ? {
            ...item,
            recommendation,
          }
        : item,
    ),
  }
}
