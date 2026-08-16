import { ArrowDown, Bot } from "lucide-react";
import { type RefObject } from "react";
import { Button, ScrollArea } from "../../../shared/components/ui";
import { type CoachMessage } from "../types";
import { CoachMessageBubble } from "./CoachMessageBubble";

export function CoachMessageList({
  scrollRef,
  messages,
  activeMessageId,
  thinking,
  isLoading,
  error,
  canLoadOlder,
  isFollowing,
  onScroll,
  onLoadOlder,
  onJumpToLatest,
  isBusy,
  onResolveUiAction,
  onDismissUiAction,
}: {
  scrollRef: RefObject<HTMLDivElement | null>;
  messages: CoachMessage[];
  activeMessageId: string | null;
  thinking: boolean;
  isLoading: boolean;
  error: string | null;
  canLoadOlder: boolean;
  isFollowing: boolean;
  onScroll: () => void;
  onLoadOlder: () => void;
  onJumpToLatest: () => void;
  isBusy: boolean;
  onResolveUiAction: (actionId: string, exercise: import('@/features/training/types').Exercise, method: 'created' | 'selected') => void;
  onDismissUiAction: (actionId: string) => void;
}) {
  return (
    <div className="relative min-h-0 flex-1">
      <ScrollArea
        className="h-full px-4 py-4"
        viewportRef={scrollRef}
        onViewportScroll={onScroll}
      >
        <div className="mx-auto grid max-w-lg gap-3">
          {canLoadOlder ? (
            <Button
              variant="outline"
              size="sm"
              type="button"
              disabled={isLoading}
              onClick={onLoadOlder}
            >
              Load older messages
            </Button>
          ) : null}
          {isLoading ? (
            <p className="text-center text-sm text-muted-foreground">
              Loading conversation...
            </p>
          ) : null}
          {!isLoading && messages.length === 0 ? (
            <div className="grid place-items-center gap-2 py-16 text-center text-sm text-muted-foreground">
              <Bot size={24} aria-hidden="true" />
              <p>Ask a question when you are ready.</p>
            </div>
          ) : null}
          {messages.map((message) => (
            <CoachMessageBubble
              key={message.id}
              message={message}
              thinking={message.id === activeMessageId && thinking}
              isBusy={isBusy}
              onResolveUiAction={onResolveUiAction}
              onDismissUiAction={onDismissUiAction}
            />
          ))}
          {error ? (
            <p
              role="alert"
              className="rounded-lg bg-destructive/10 px-3 py-2 text-sm text-destructive"
            >
              {error}
            </p>
          ) : null}
        </div>
      </ScrollArea>
      {!isFollowing && messages.length ? (
        <Button
          className="absolute bottom-3 left-1/2 -translate-x-1/2 rounded-full shadow-md"
          size="sm"
          type="button"
          onClick={onJumpToLatest}
        >
          <ArrowDown size={16} aria-hidden="true" /> Latest
        </Button>
      ) : null}
    </div>
  );
}
