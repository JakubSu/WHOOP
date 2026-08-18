import { useEffect, useRef, type KeyboardEvent, type SyntheticEvent } from "react";
import { Send } from "lucide-react";
import { Button, Input } from "../../../shared/components/ui";

const DESKTOP_COMPOSER_MAX_HEIGHT = 160;

export function CoachComposer({
  value,
  isLoading,
  isStreaming,
  onChange,
  onSubmit,
}: {
  value: string;
  isLoading: boolean;
  isStreaming: boolean;
  onChange: (value: string) => void;
  onSubmit: () => void;
}) {
  const desktopTextareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    const textarea = desktopTextareaRef.current;
    if (!textarea || !window.matchMedia("(min-width: 64rem)").matches) return;

    textarea.style.height = "auto";
    textarea.style.height = `${Math.min(textarea.scrollHeight, DESKTOP_COMPOSER_MAX_HEIGHT)}px`;
  }, [value]);

  function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }

  function submitFromTextarea(event: KeyboardEvent<HTMLTextAreaElement>) {
    if ((event.ctrlKey || event.metaKey) && event.key === "Enter") {
      event.preventDefault();
      onSubmit();
    }
  }

  return (
    <form
      className="flex shrink-0 items-end gap-2 border-t border-border bg-card px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3"
      onSubmit={submit}
      data-tour="coach-composer"
    >
      <Input
        className="lg:hidden"
        aria-label="Message coach"
        value={value}
        placeholder={isStreaming ? "Coach is working..." : "Message coach"}
        disabled={isLoading}
        onChange={(event) => onChange(event.target.value)}
      />
      <textarea
        ref={desktopTextareaRef}
        className="hidden min-h-11 w-full resize-none overflow-y-auto rounded-md border border-input bg-background px-3 py-2.5 text-sm outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 lg:block lg:max-h-40"
        aria-label="Message coach"
        rows={1}
        value={value}
        placeholder={isStreaming ? "Coach is working..." : "Message coach"}
        disabled={isLoading}
        onChange={(event) => onChange(event.target.value)}
        onKeyDown={submitFromTextarea}
      />
      <Button
        size="icon"
        type="submit"
        aria-label="Send message"
        disabled={isStreaming || isLoading || !value.trim()}
        data-tour="coach-send"
      >
        <Send size={18} aria-hidden="true" />
      </Button>
    </form>
  );
}
