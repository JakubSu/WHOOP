import { Sparkles } from "lucide-react";

export function CoachCollapsedBar({
  label,
  isStreaming,
  onOpen,
}: {
  label: string;
  isStreaming: boolean;
  onOpen: () => void;
}) {
  return (
    <button
      className="fixed inset-x-3 bottom-[max(0.75rem,env(safe-area-inset-bottom))] z-30 mx-auto flex w-auto max-w-lg items-center gap-2 rounded-full bg-primary px-4 py-3 text-sm font-semibold text-primary-foreground shadow-lg transition-transform active:scale-[0.98] sm:inset-x-6"
      type="button"
      onClick={onOpen}
      data-tour="coach-open"
    >
      <Sparkles size={18} aria-hidden="true" />
      <span>{isStreaming ? "Coach is thinking" : `Coach - ${label}`}</span>
    </button>
  );
}
