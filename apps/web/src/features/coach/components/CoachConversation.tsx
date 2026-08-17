import { type RefObject } from 'react'
import { CoachComposer } from './CoachComposer'
import { CoachMessageList } from './CoachMessageList'
import { CoachSheetHeader } from './CoachSheetHeader'
import { type CoachMessage, type CoachConversationSummary } from '../types'
import { type Exercise } from '../../training/types'

type CoachConversationProps = {
  label: string; conversations: CoachConversationSummary[]; conversationId: string | null; messages: CoachMessage[]; activeMessageId: string | null; thinking: boolean; value: string; isLoading: boolean; isStreaming: boolean; error: string | null; canLoadOlder: boolean; isFollowing: boolean; scrollRef: RefObject<HTMLDivElement | null>; onSelect: (conversationId: string) => void; onNewChat: () => void; onCollapse: () => void; onExpand?: () => void; onChange: (value: string) => void; onSubmit: () => void; onScroll: () => void; onLoadOlder: () => void; onJumpToLatest: () => void; isBusy: boolean; onResolveUiAction: (actionId: string, exercise: Exercise, method: 'created' | 'selected') => void; onDismissUiAction: (actionId: string) => void
}

export function CoachConversation(props: CoachConversationProps) {
  return <>
    <CoachSheetHeader label={props.label} conversations={props.conversations} conversationId={props.conversationId} isBusy={props.isLoading || props.isStreaming} onSelect={props.onSelect} onNewChat={props.onNewChat} onCollapse={props.onCollapse} onExpand={props.onExpand} />
    <CoachMessageList scrollRef={props.scrollRef} messages={props.messages} activeMessageId={props.activeMessageId} thinking={props.thinking} isLoading={props.isLoading} error={props.error} canLoadOlder={props.canLoadOlder} isFollowing={props.isFollowing} onScroll={props.onScroll} onLoadOlder={props.onLoadOlder} onJumpToLatest={props.onJumpToLatest} isBusy={props.isBusy} onResolveUiAction={props.onResolveUiAction} onDismissUiAction={props.onDismissUiAction} />
    <CoachComposer value={props.value} isLoading={props.isLoading} isStreaming={props.isStreaming} onChange={props.onChange} onSubmit={props.onSubmit} />
  </>
}
