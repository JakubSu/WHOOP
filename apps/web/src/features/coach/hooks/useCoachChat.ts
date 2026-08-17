import { useCallback, useState } from 'react'
import { createCoachConversation, dismissCoachUiAction, getCoachMessages, listCoachConversations, resolveCoachUiAction, streamCoachMessage } from '../api/coachApi'
import { applyCoachStreamEvent, type CoachChatState } from '../services/coachOverlayState'
import { type CoachConversationSummary, type CoachMessage, type CoachStreamEvent } from '../types'
import { type CoachViewContext } from '../services/coachContext'

const EMPTY_CHAT: CoachChatState = { messages: [], activeMessageId: null, thinking: false }

export function useCoachChat({ currentContext, onSend, onBeforeLoadOlder }: { currentContext: CoachViewContext | null; onSend: () => void; onBeforeLoadOlder: () => void }) {
  const [conversationId, setConversationId] = useState<string | null>(null)
  const [conversations, setConversations] = useState<CoachConversationSummary[]>([])
  const [chat, setChat] = useState<CoachChatState>(EMPTY_CHAT)
  const [input, setInput] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [isStreaming, setIsStreaming] = useState(false)
  const [streamVersion, setStreamVersion] = useState(0)
  const [error, setError] = useState<string | null>(null)
  const [nextMessageCursor, setNextMessageCursor] = useState<string | null>(null)

  const loadLatestConversation = useCallback(async () => {
    setIsLoading(true); setError(null)
    try {
      const page = await listCoachConversations()
      setConversations(page.results)
      const latest = page.results[0]
      if (!latest) { setConversationId(null); setChat(EMPTY_CHAT); setNextMessageCursor(null); return }
      const messages = await getCoachMessages(latest.id)
      setConversationId(latest.id); setNextMessageCursor(messages.next)
      setChat({ messages: messages.results, activeMessageId: null, thinking: false })
    } catch (reason) { setError(errorMessage(reason)) } finally { setIsLoading(false) }
  }, [])

  const selectConversation = useCallback(async (nextConversationId: string) => {
    if (isStreaming || nextConversationId === conversationId) return
    setIsLoading(true); setError(null)
    try {
      const page = await getCoachMessages(nextConversationId)
      setConversationId(nextConversationId); setNextMessageCursor(page.next)
      setChat({ messages: page.results, activeMessageId: null, thinking: false })
    } catch (reason) { setError(errorMessage(reason)) } finally { setIsLoading(false) }
  }, [conversationId, isStreaming])

  const newChat = useCallback(async () => {
    if (isStreaming) return
    setIsLoading(true); setError(null)
    try {
      const conversation = await createCoachConversation()
      setConversationId(conversation.id)
      setConversations((items) => [{ id: conversation.id, title: conversation.title, last_message_preview: null, updated_at: conversation.updated_at }, ...items])
      setNextMessageCursor(null); setChat(EMPTY_CHAT)
    } catch (reason) { setError(errorMessage(reason)) } finally { setIsLoading(false) }
  }, [isStreaming])

  const send = useCallback(async () => {
    const content = input.trim()
    if (!content || isStreaming || isLoading) return
    setInput(''); setError(null); setIsStreaming(true); onSend()
    const localMessage: CoachMessage = { id: `local-${crypto.randomUUID()}`, role: 'user', content, created_at: new Date().toISOString(), activities: [], recommendation: null, ui_actions: [] }
    setChat((state) => ({ ...state, messages: [...state.messages, localMessage] }))
    try {
      let activeConversationId = conversationId
      if (!activeConversationId) {
        const conversation = await createCoachConversation()
        activeConversationId = conversation.id
        setConversationId(activeConversationId)
        setConversations((items) => [{ id: conversation.id, title: conversation.title, last_message_preview: null, updated_at: conversation.updated_at }, ...items])
      }
      await streamCoachMessage({ conversationId: activeConversationId, content, viewContext: currentContext, onEvent: applyStreamEvent })
    } catch (reason) { setError(errorMessage(reason)) } finally { setIsStreaming(false) }
  }, [conversationId, currentContext, input, isLoading, isStreaming, onSend])

  const applyStreamEvent = useCallback((event: CoachStreamEvent) => {
    if (event.event === 'error') setError(event.data.message)
    setChat((state) => applyCoachStreamEvent(state, event))
    setStreamVersion((version) => version + 1)
  }, [])

  const loadOlderMessages = useCallback(async () => {
    if (!conversationId || !nextMessageCursor || isLoading) return
    onBeforeLoadOlder(); setIsLoading(true)
    try {
      const page = await getCoachMessages(conversationId, nextMessageCursor)
      setChat((state) => ({ ...state, messages: [...page.results, ...state.messages] }))
      setNextMessageCursor(page.next)
    } catch (reason) { setError(errorMessage(reason)) } finally { setIsLoading(false) }
  }, [conversationId, isLoading, nextMessageCursor, onBeforeLoadOlder])

  const resolveUiAction = useCallback(async (actionId: string, exerciseId: string, method: 'created' | 'selected') => {
    if (!conversationId || isStreaming) return
    setError(null); setIsStreaming(true); onSend()
    try { await resolveCoachUiAction({ conversationId, actionId, exerciseId, method, onEvent: applyStreamEvent }) }
    catch (reason) { setError(errorMessage(reason)) } finally { setIsStreaming(false) }
  }, [applyStreamEvent, conversationId, isStreaming, onSend])

  const dismissUiAction = useCallback(async (actionId: string) => {
    if (!conversationId || isStreaming) return
    try {
      const message = await dismissCoachUiAction(conversationId, actionId)
      setChat((state) => ({ ...state, messages: state.messages.map((item) => item.id === message.id ? message : item) }))
    } catch (reason) { setError(errorMessage(reason)) }
  }, [conversationId, isStreaming])

  return { conversationId, conversations, messages: chat.messages, activeMessageId: chat.activeMessageId, thinking: chat.thinking, input, setInput, isLoading, isStreaming, streamVersion, error, nextMessageCursor, loadLatestConversation, selectConversation, newChat, send, loadOlderMessages, resolveUiAction, dismissUiAction }
}

function errorMessage(reason: unknown) { return reason instanceof Error ? reason.message : 'I couldn’t complete that request.' }
