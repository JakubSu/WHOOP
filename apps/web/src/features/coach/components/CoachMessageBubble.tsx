import { Bot, Check, CircleAlert, LoaderCircle, Wrench } from "lucide-react";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import { type CoachMessage } from "../types";
import { CoachRecommendationCard } from "./CoachRecommendationCard";

export function CoachMessageBubble({
  message,
  thinking,
}: {
  message: CoachMessage;
  thinking: boolean;
}) {
  return (
    <article
      className={`max-w-[88%] rounded-2xl px-3 py-2 text-sm ${message.role === "user" ? "ml-auto bg-primary text-primary-foreground" : "mr-auto bg-muted text-foreground"}`}
    >
      {message.activities.length ? (
        <section
          className="mb-3 border-b border-border/60 pb-3 text-xs"
          aria-label="Tool calls"
        >
          <p className="mb-2 flex items-center gap-1.5 font-medium text-muted-foreground">
            <Wrench size={14} aria-hidden="true" /> Tool calls
          </p>
          <ul className="grid gap-1.5">
            {message.activities.map((activity) => (
              <li key={activity.id} className="flex items-center gap-2">
                <ToolCallStatus status={activity.status} />
                <span>{activity.label}</span>
              </li>
            ))}
          </ul>
        </section>
      ) : null}
      {message.content ? (
        <ReactMarkdown remarkPlugins={[remarkGfm]}>
          {message.content}
        </ReactMarkdown>
      ) : thinking ? (
        <span className="flex items-center gap-2">
          <Bot size={16} aria-hidden="true" /> Thinking...
        </span>
      ) : null}
      {message.recommendation ? (
        <CoachRecommendationCard recommendation={message.recommendation} />
      ) : null}
    </article>
  );
}

function ToolCallStatus({
  status,
}: {
  status: CoachMessage["activities"][number]["status"];
}) {
  if (status === "running")
    return (
      <LoaderCircle
        className="size-3.5 animate-spin motion-reduce:animate-none"
        aria-label="Running"
      />
    );
  if (status === "failed")
    return (
      <CircleAlert className="size-3.5 text-destructive" aria-label="Failed" />
    );
  return (
    <Check
      className="size-3.5 text-emerald-600 dark:text-emerald-400"
      aria-label="Completed"
    />
  );
}
