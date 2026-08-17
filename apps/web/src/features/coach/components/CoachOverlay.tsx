import { useCallback, useEffect, useRef, useState } from 'react'
import { Sparkles } from 'lucide-react'
import { Button } from '../../../shared/components/ui'
import { useCoachPanel } from '../context/CoachPanelContext'
import { useCoachOverlayContext } from '../context/CoachOverlayContext'
import { useCoachAutoScroll } from '../hooks/useCoachAutoScroll'
import { useCoachBottomSheet } from '../hooks/useCoachBottomSheet'
import { useCoachChat } from '../hooks/useCoachChat'
import { labelForCoachContext } from '../services/coachContext'
import { CoachBottomSheet } from './CoachBottomSheet'
import { CoachCollapsedBar } from './CoachCollapsedBar'
import { CoachConversation } from './CoachConversation'

export function CoachOverlay() {
  const { currentContext } = useCoachOverlayContext()
  const desktop = useCoachPanel()
  const isDesktop = useDesktopViewport()
  const sheet = useCoachBottomSheet(true)
  const startFollowingRef = useRef<() => void>(() => {})
  const prepareForPrependRef = useRef<() => void>(() => {})
  const hasLoadedDesktopConversationRef = useRef(false)
  const chat = useCoachChat({ currentContext, onSend: () => startFollowingRef.current(), onBeforeLoadOlder: () => prepareForPrependRef.current() })
  const autoScroll = useCoachAutoScroll({ isOpen: sheet.isOpen || desktop.mode !== 'collapsed', messageCount: chat.messages.length, isStreaming: chat.isStreaming, streamVersion: chat.streamVersion })
  startFollowingRef.current = autoScroll.startFollowing
  prepareForPrependRef.current = autoScroll.prepareForPrepend
  const label = labelForCoachContext(currentContext)
  const isBusy = chat.isLoading || chat.isStreaming

  useEffect(() => {
    if (
      !isDesktop ||
      desktop.mode === 'collapsed' ||
      hasLoadedDesktopConversationRef.current ||
      chat.conversationId ||
      chat.messages.length > 0
    ) return

    hasLoadedDesktopConversationRef.current = true
    void chat.loadLatestConversation()
  }, [chat.conversationId, chat.loadLatestConversation, chat.messages.length, desktop.mode, isDesktop])

  const openCoach = useCallback(() => {
    sheet.open()
    desktop.open()
    if (!chat.conversationId && chat.messages.length === 0) void chat.loadLatestConversation()
  }, [chat, desktop, sheet])

  const conversation = <CoachConversation label={label} conversations={chat.conversations} conversationId={chat.conversationId} messages={chat.messages} activeMessageId={chat.activeMessageId} thinking={chat.thinking} value={chat.input} isLoading={chat.isLoading} isStreaming={chat.isStreaming} error={chat.error} canLoadOlder={Boolean(chat.nextMessageCursor)} isFollowing={autoScroll.isFollowing} scrollRef={autoScroll.scrollRef} onSelect={(id) => void chat.selectConversation(id)} onNewChat={() => void chat.newChat()} onCollapse={isDesktop ? desktop.collapse : sheet.close} onExpand={isDesktop && desktop.mode === 'open' ? desktop.expand : undefined} onChange={chat.setInput} onSubmit={() => void chat.send()} onScroll={autoScroll.onScroll} onLoadOlder={() => void chat.loadOlderMessages()} onJumpToLatest={autoScroll.scrollToLatest} isBusy={isBusy} onResolveUiAction={(actionId, exercise, method) => void chat.resolveUiAction(actionId, exercise.id, method)} onDismissUiAction={(actionId) => void chat.dismissUiAction(actionId)} />

  return <div className="contents" aria-live={chat.isStreaming ? 'polite' : 'off'}>
    {!isDesktop ? <div className="lg:hidden">
      {!sheet.isOpen ? <CoachCollapsedBar label={label} isStreaming={chat.isStreaming} onOpen={openCoach} /> : null}
      <CoachBottomSheet open={sheet.isOpen} onOpenChange={(open) => open ? openCoach() : sheet.close()} onDragStart={sheet.onDragStart} onDragEnd={sheet.onDragEnd}>{conversation}</CoachBottomSheet>
    </div> : null}
    {isDesktop ? <aside className="relative min-h-0 border-l border-border bg-card">
      {desktop.mode === 'collapsed' ? <Button className="m-1 size-10" variant="ghost" size="icon" type="button" aria-label="Open coach" onClick={openCoach}><Sparkles size={19} aria-hidden="true" /></Button> : null}
      {desktop.mode !== 'collapsed' ? <div className={desktop.mode === 'expanded' ? 'absolute inset-y-0 right-0 z-20 flex w-[34rem] flex-col border-l border-border bg-card shadow-2xl' : 'flex h-full flex-col'}>{conversation}</div> : null}
    </aside> : null}
  </div>
}

function useDesktopViewport() {
  const [isDesktop, setIsDesktop] = useState(false)
  useEffect(() => {
    const query = window.matchMedia('(min-width: 1024px)')
    const update = () => setIsDesktop(query.matches)
    update()
    query.addEventListener('change', update)
    return () => query.removeEventListener('change', update)
  }, [])
  return isDesktop
}
