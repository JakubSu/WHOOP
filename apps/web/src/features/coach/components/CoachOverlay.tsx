import { useCallback, useRef } from "react";
import { useCoachChat } from "../hooks/useCoachChat";
import { useCoachAutoScroll } from "../hooks/useCoachAutoScroll";
import { useCoachBottomSheet } from "../hooks/useCoachBottomSheet";
import { useCoachOverlayContext } from "../context/CoachOverlayContext";
import { labelForCoachContext } from "../services/coachContext";
import { CoachBottomSheet } from "./CoachBottomSheet";
import { CoachCollapsedBar } from "./CoachCollapsedBar";
import { CoachComposer } from "./CoachComposer";
import { CoachMessageList } from "./CoachMessageList";
import { CoachSheetHeader } from "./CoachSheetHeader";

export function CoachOverlay() {
  const { currentContext } = useCoachOverlayContext();
  const sheet = useCoachBottomSheet(Boolean(currentContext));
  const startFollowingRef = useRef<() => void>(() => {});
  const prepareForPrependRef = useRef<() => void>(() => {});
  const chat = useCoachChat({
    onSend: () => startFollowingRef.current(),
    onBeforeLoadOlder: () => prepareForPrependRef.current(),
  });
  const autoScroll = useCoachAutoScroll({
    isOpen: sheet.isOpen,
    messageCount: chat.messages.length,
    isStreaming: chat.isStreaming,
    streamVersion: chat.streamVersion,
  });
  startFollowingRef.current = autoScroll.startFollowing;
  prepareForPrependRef.current = autoScroll.prepareForPrepend;

  const openCoach = useCallback(() => {
    sheet.open();
    if (!chat.conversationId && chat.messages.length === 0)
      void chat.loadLatestConversation();
  }, [chat, sheet]);

  if (!currentContext) return null;
  const label = labelForCoachContext(currentContext);
  const isBusy = chat.isLoading || chat.isStreaming;

  return (
    <div aria-live={chat.isStreaming ? "polite" : "off"}>
      {!sheet.isOpen ? (
        <CoachCollapsedBar
          label={label}
          isStreaming={chat.isStreaming}
          onOpen={openCoach}
        />
      ) : null}
      <CoachBottomSheet
        open={sheet.isOpen}
        onOpenChange={(open) => (open ? openCoach() : sheet.close())}
        onDragStart={sheet.onDragStart}
        onDragEnd={sheet.onDragEnd}
      >
        <CoachSheetHeader
          label={label}
          conversations={chat.conversations}
          conversationId={chat.conversationId}
          isBusy={isBusy}
          onSelect={(conversationId) =>
            void chat.selectConversation(conversationId)
          }
          onNewChat={() => void chat.newChat()}
          onCollapse={sheet.close}
        />
        <CoachMessageList
          scrollRef={autoScroll.scrollRef}
          messages={chat.messages}
          activeMessageId={chat.activeMessageId}
          thinking={chat.thinking}
          isLoading={chat.isLoading}
          error={chat.error}
          canLoadOlder={Boolean(chat.nextMessageCursor)}
          isFollowing={autoScroll.isFollowing}
          onScroll={autoScroll.onScroll}
          onLoadOlder={() => void chat.loadOlderMessages()}
          onJumpToLatest={() => autoScroll.scrollToLatest()}
          isBusy={isBusy}
          onResolveUiAction={(actionId, exercise, method) => void chat.resolveUiAction(actionId, exercise.id, method)}
          onDismissUiAction={(actionId) => void chat.dismissUiAction(actionId)}
        />
        <CoachComposer
          value={chat.input}
          isLoading={chat.isLoading}
          isStreaming={chat.isStreaming}
          onChange={chat.setInput}
          onSubmit={() => void chat.send()}
        />
      </CoachBottomSheet>
    </div>
  );
}
