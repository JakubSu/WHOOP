import { useCallback, useState } from 'react'
import { createCoachConversation, getCoachMessages, listCoachConversations, streamCoachMessage } from '../api/coachApi'
import { applyCoachStreamEvent, type CoachChatState } from '../services/coachOverlayState'
import { type CoachConversationSummary, type CoachMessage, type CoachStreamEvent } from '../types'

const EMPTY_CHAT: CoachChatState = { messages: [], activeMessageId: null, thinking: false }

export function useCoachChat({ onSend, onBeforeLoadOlder }: { onSend: () => void; onBeforeLoadOlder: () => void }) {
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
    const localMessage: CoachMessage = { id: `local-${crypto.randomUUID()}`, role: 'user', content, created_at: new Date().toISOString(), activities: [], recommendation: null }
    setChat((state) => ({ ...state, messages: [...state.messages, localMessage] }))
    try {
      let activeConversationId = conversationId
      if (!activeConversationId) {
        const conversation = await createCoachConversation()
        activeConversationId = conversation.id
        setConversationId(activeConversationId)
        setConversations((items) => [{ id: conversation.id, title: conversation.title, last_message_preview: null, updated_at: conversation.updated_at }, ...items])
      }
      await streamCoachMessage({ conversationId: activeConversationId, content, onEvent: applyStreamEvent })
    } catch (reason) { setError(errorMessage(reason)) } finally { setIsStreaming(false) }
  }, [conversationId, input, isLoading, isStreaming, onSend])

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

  return { conversationId, conversations, messages: chat.messages, activeMessageId: chat.activeMessageId, thinking: chat.thinking, input, setInput, isLoading, isStreaming, streamVersion, error, nextMessageCursor, loadLatestConversation, selectConversation, newChat, send, loadOlderMessages }
}

function errorMessage(reason: unknown) { return reason instanceof Error ? reason.message : 'I couldn’t complete that request.' }
