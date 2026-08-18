import { type SyntheticEvent } from "react";
import { Send } from "lucide-react";
import { Button, Input } from "../../../shared/components/ui";

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
  function submit(event: SyntheticEvent<HTMLFormElement>) {
    event.preventDefault();
    onSubmit();
  }
  return (
    <form
      className="flex shrink-0 gap-2 border-t border-border bg-card px-4 pb-[max(1rem,env(safe-area-inset-bottom))] pt-3"
      onSubmit={submit}
      data-tour="coach-composer"
    >
      <Input
        aria-label="Message coach"
        value={value}
        placeholder={isStreaming ? "Coach is working..." : "Message coach"}
        disabled={isLoading}
        onChange={(event) => onChange(event.target.value)}
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
