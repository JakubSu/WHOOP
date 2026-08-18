import { Maximize2, Minimize2, Plus } from "lucide-react";
import { Button } from "../../../shared/components/ui";
import { type CoachConversationSummary } from "../types";

type Props = {
  label: string;
  conversations: CoachConversationSummary[];
  conversationId: string | null;
  isBusy: boolean;
  onSelect: (conversationId: string) => void;
  onNewChat: () => void;
  onCollapse?: () => void;
  onExpand?: () => void;
};

export function CoachSheetHeader({
  label,
  conversations,
  conversationId,
  isBusy,
  onSelect,
  onNewChat,
  onCollapse,
  onExpand,
}: Props) {
  return (
    <header className="flex shrink-0 items-start justify-between gap-3 border-b border-border px-4 pb-3 lg:px-6 lg:pb-4 lg:pt-5">
      <div className="min-w-0">
        <p className="text-xs font-semibold uppercase tracking-wider text-primary">
          Coach - {label}
        </p>
        <h2 className="mt-1 text-lg font-bold">Your training coach</h2>
        {conversations.length ? (
          <select
            className="mt-2 max-w-full rounded-md border border-input bg-background px-2 py-1 text-base sm:text-xs"
            aria-label="Coach conversation history"
            value={conversationId ?? ""}
            disabled={isBusy}
            onChange={(event) => onSelect(event.target.value)}
          >
            {conversations.map((conversation) => (
              <option key={conversation.id} value={conversation.id}>
                {conversation.title ??
                  conversation.last_message_preview ??
                  "New conversation"}
              </option>
            ))}
          </select>
        ) : null}
      </div>
      <div className="flex shrink-0 gap-1">
        <Button
          variant="ghost"
          size="icon"
          type="button"
          aria-label="New chat"
          disabled={isBusy}
          onClick={onNewChat}
        >
          <Plus size={18} aria-hidden="true" />
        </Button>
        {onExpand ? (
          <Button
            variant="ghost"
            size="icon"
            type="button"
            aria-label="Expand coach"
            onClick={onExpand}
          >
            <Maximize2 size={18} aria-hidden="true" />
          </Button>
        ) : null}
        {onCollapse ? (
          <Button
            variant="ghost"
            size="icon"
            type="button"
            aria-label="Restore coach size"
            onClick={onCollapse}
            data-tour="coach-close"
          >
            <Minimize2 size={18} aria-hidden="true" />
          </Button>
        ) : null}
      </div>
    </header>
  );
}
