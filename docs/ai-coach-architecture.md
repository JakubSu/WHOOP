# AI Coach Architecture

## Status

Accepted for MVO design.

## Goal

Build a single page-aware AI coach that gives the user a live Codex-like chat
experience. The coach explains WHOOP metrics and workout recommendations,
answers follow-up questions, and proposes workout changes. Workout changes are
never applied directly by the model; they become validated recommendation
operations that the user can approve or reject.

## Decisions

- Use one page-aware coach, not separate coaches per page.
- Use Server-Sent Events for the MVO coach turn experience.
- Stream visible progress and tool activity, not hidden model reasoning.
- Use a deterministic context-first workflow for the MVO.
- Scope conversations to the current page/session context.
- Treat UI actions as backend-authorized commands with strict allowlists.
- From the training plan page, explain and navigate first; modify workouts only
  from an individual workout context.
- Represent workout changes as explicit patch operations using the existing
  recommendation operation model.
- Store coach workout-change proposals as normal `Recommendation` records.
- Persist conversation domain data in `coaching`.
- Keep AI prompt/tool orchestration in `ai.coach`.
- Include compact pending/recent recommendation context in coach prompts.
- Do not introduce a full goals/preferences subsystem in the MVO.
- Treat pain or injury language as a temporary constraint plus a safety
  boundary, not as medical advice.
- Persist final messages and key artifacts, not every streamed event.
- Keep the opened coach chat on its current conversation during navigation.
  Show a subtle current-screen context indicator, and send the latest
  `page_context` only when the user submits the next message.
- On first open for a coach-capable screen, load persisted messages for the
  active conversation when one exists. If no conversation exists for that screen
  context, show an empty starter state.

## Existing System Fit

The current repo already has the right bounded contexts:

- `training`: owns exercises, workouts, workout exercises, and training plans.
- `whoop`: owns WHOOP OAuth, snapshots, summaries, and external API access.
- `recommendation`: owns workout patch proposals, operation validation, and
  operation-level approval/rejection.
- `coaching`: should own conversation persistence and the coach API.
- `ai`: owns model/provider infrastructure, prompts, and structured generation.

The MVO should extend these contexts rather than introduce a separate agent data
model.

## Backend Module Plan

```text
services/api/
  coaching/
    models.py
    services.py
    api/
      urls.py
      views.py
      serializers.py

  ai/
    coach/
      orchestrator.py
      context.py
      events.py
      schemas.py
      safety.py
      ui_actions.py
      prompts/
        coach_turn.v1.md
```

## Domain Models

### `coaching.models.CoachConversation`

Owns a page/session-scoped conversation.

Fields:

- `id`
- `user_id`
- `page_type`: `today_workout`, `workout`, `training_plan`, `recovery`
- `context_id`: workout ID, plan ID, or blank
- `status`: `active`, `archived`
- `created_at`
- `updated_at`
- `last_message_at`

Recommended indexes:

- `(user_id, page_type, context_id, status)`
- `(user_id, last_message_at)`

### `coaching.models.CoachMessage`

Owns durable chat history.

Fields:

- `id`
- `conversation`
- `role`: `user`, `assistant`
- `content`
- `metadata_json`
- `recommendation_id`: nullable UUID for proposals created by this message
- `created_at`

Do not persist every SSE event as a row. Store only the final user message,
final assistant message, safety flags, UI actions that matter, and linked
recommendations.

### `recommendation.models.Recommendation`

Reuse this model for coach proposals. Add only lightweight source/link fields if
needed:

- `source`: `daily_recommendation`, `coach_chat`
- `coach_conversation_id`: nullable UUID
- `coach_message_id`: nullable UUID

The existing `RecommendationOperation` lifecycle remains the approval boundary.

## API Contract

Base path:

```http
/api/v1/coach/
```

### Start Or Continue Streamed Turn

```http
POST /api/v1/coach/turns/stream/
Accept: text/event-stream
Authorization: Bearer <token>
```

Request:

```json
{
  "conversation_id": "optional-existing-conversation-id",
  "page_context": {
    "page_type": "workout",
    "context_id": "workout-uuid"
  },
  "message": "Make today's workout easier because my knee hurts."
}
```

Behavior:

1. Validate user authentication.
2. Validate `page_context`.
3. Reuse or create the active session-scoped `CoachConversation`.
4. Persist the user `CoachMessage`.
5. Run the deterministic coach turn.
6. Stream progress/tool/action/final events.
7. Persist the assistant `CoachMessage`.
8. Link any created `Recommendation`.

### List Conversation Messages

```http
GET /api/v1/coach/conversations/:conversationId/messages/
```

Returns persisted user/assistant messages and linked recommendation IDs. This is
for loading prior chat history, not replaying old stream events.

### Get Active Conversation For Page Context

```http
GET /api/v1/coach/conversations/active/?page_type=workout&context_id=workout-uuid
```

Returns `200` with the active conversation summary and messages when an active
conversation exists for the authenticated user and page context. Returns `204`
when no conversation exists, allowing the frontend to show an empty starter
state without creating a conversation before the user's first message.

## SSE Event Types

Events use named SSE events with JSON payloads.

### `conversation_started`

```json
{
  "conversation_id": "uuid",
  "page_context": {
    "page_type": "workout",
    "context_id": "workout-uuid"
  }
}
```

### `assistant_progress`

Visible progress summary. This is not hidden chain-of-thought.

```json
{
  "message": "I'll compare your recovery, recent strain, and this workout."
}
```

### `tool_call_started`

```json
{
  "tool": "get_whoop_summary",
  "label": "Reading WHOOP summary"
}
```

### `tool_call_completed`

Return compact, sanitized summaries, not raw payload dumps.

```json
{
  "tool": "get_whoop_summary",
  "summary": "Recovery 42%, sleep 71%, day strain 11.2."
}
```

### `assistant_delta`

Optional streamed answer text.

```json
{
  "text": "Your recovery is lower today, so I would avoid pushing lower-body volume."
}
```

### `recommendation_created`

```json
{
  "recommendation": {
    "id": "uuid",
    "status": "pending",
    "operations": []
  }
}
```

### `ui_action`

Only backend-authorized actions are emitted.

```json
{
  "action": {
    "type": "navigate",
    "route": "/workouts/workout-uuid"
  }
}
```

### `assistant_done`

```json
{
  "message": {
    "id": "uuid",
    "role": "assistant",
    "content": "I recommend reducing today's knee-demanding work..."
  }
}
```

### `error`

```json
{
  "code": "coach_turn_failed",
  "message": "I could not complete that coach turn."
}
```

## Deterministic MVO Turn Flow

```text
Frontend sends message
  |
  v
CoachTurnStreamAPIView
  |
  v
StartCoachTurnService
  - validates page context
  - stores user message
  - opens SSE generator
  |
  v
CoachOrchestrator.run_turn()
  - emits progress events
  - builds deterministic context
  - asks model for structured coach response
  - validates UI actions
  - validates/stores recommendation if needed
  - emits final events
  |
  v
StartCoachTurnService
  - stores assistant message
  - links recommendation
```

## Context Builders

`ai.coach.context.CoachContextBuilder` should compose page-aware context from
existing services.

### Shared Context

- Recent conversation messages for this conversation.
- Current page context.
- Latest WHOOP summary via `whoop.services.create_summary_service().execute`.
- Compact pending/recent recommendation context.

### Workout Context

For `page_type = workout`:

- Current workout snapshot using the same shape as
  `recommendation.services.build_workout_recommendation_context`.
- Workout exercise display data.
- Available exercises.
- Pending recommendation operations for this workout.

Workout modifications are allowed only in this context.

### Today Workout Context

For `page_type = today_workout`:

- Use `training.services.workout.get_workout_landing`.
- If the landing workout is today's workout, treat it like workout context.
- If no workout exists today, answer questions and optionally navigate to the
  nearest workout, but do not create ambiguous modifications.

### Training Plan Context

For `page_type = training_plan`:

- Plan summary.
- List of plan workouts.
- WHOOP summary.
- Conversation history.

The coach may explain the plan and emit navigation actions to a workout. It
should not create workout patch recommendations from this context in the MVO.

### Recovery Context

For `page_type = recovery`:

- WHOOP summary.
- Recent workouts from the WHOOP summary payload.
- Conversation history.

The coach may answer recovery questions and navigate to relevant workouts when
the backend can validate the target.

## AI Schemas

`ai.coach.schemas.CoachTurnDraft` should be the model-facing structured output.

Fields:

- `answer`: final assistant message.
- `progress_summaries`: optional short visible summaries.
- `workout_patch`: optional `WorkoutPatchDraft`.
- `ui_actions`: optional proposed structured actions.
- `safety_flags`: optional list, such as `pain_or_injury_mentioned`.

For workout modifications, reuse:

- `ai.recommendation.schemas.WorkoutPatchDraft`
- `ai.recommendation.schemas.WorkoutPatchOperation`

## Coach Tools

The MVO can expose deterministic tool events without allowing a free-running
agent loop.

Read steps:

- `get_whoop_summary`
- `get_workout_context`
- `get_training_plan_context`
- `get_recommendation_context`
- `list_exercises`

Write/proposal step:

- `propose_workout_changes`

`propose_workout_changes` does not write workouts. It validates a
`WorkoutPatchDraft`, creates a `Recommendation`, and returns pending operations
for user approval.

## UI Actions

Model-proposed UI actions must be symbolic, not raw routes.

Allowed proposed action:

```json
{
  "type": "navigate",
  "target": "workout",
  "id": "workout-uuid"
}
```

`ai.coach.ui_actions.AuthorizeUiActionService` should:

- check action type is allowed
- check target type is allowed
- check the entity exists
- check the entity belongs to the user
- generate the frontend route in backend code

Only authorized actions become `ui_action` SSE events.

## Safety Boundary

Pain or injury language should be handled as a temporary constraint in the
current turn.

The coach may:

- suggest lower-load or lower-irritation substitutions
- reduce volume or intensity
- suggest skipping painful work
- recommend consulting a clinician for sharp, worsening, or gait-altering pain

The coach must not:

- diagnose an injury
- provide rehab protocols
- claim a medical cause
- imply WHOOP metrics can identify medical conditions

This belongs in the coach prompt and `ai.coach.safety`, not in a full injury
domain model for the MVO.

## Frontend Integration

Add a shared coach panel/component that can be opened from:

- Today's Workout
- Individual Workout
- Training Plan
- Recovery/WHOOP

The closed coach launcher is fixed at the bottom of the phone UI. Opening it
rolls the coach into a roughly 90%-height overlay. The opened overlay survives
screen switches and navigation. Navigation does not immediately swap the visible
conversation; instead, the UI keeps the current conversation visible, displays a
subtle indicator for the current screen context, and includes the latest
`page_context` on the next submitted turn.

The collapsed launcher should show a compact coach label with the current
screen context, such as `Coach · Today` or `Coach · Plan`. For the MVO, do not
show message previews or unread state. If a turn is streaming while the coach is
collapsed, show a small active state such as `Coach is thinking`.

The coach should allow only one active streamed turn at a time. While a turn is
streaming, disable the input and send button and show the active thinking state.

If the user submits a message after navigating to a different coach context, the
frontend switches to the conversation for the latest `page_context` before
sending. It should load that conversation if it exists, or start an empty one if
it does not, then append the new user message there. This keeps the visible chat
stable while reading, but ensures every submitted turn belongs to the backend
conversation scope for the current screen.

For the MVO, show the coach launcher only on screens that can produce a valid
coach `page_context`: Today's Workout (`/training`), Individual Workout
(`/workouts/:workoutId`), Training Plan (`/plan`), and the future
Recovery/WHOOP screen. Hide it on authentication, WHOOP connection, and any
screen without a valid page context.

On first open for a coach-capable screen, the frontend should look up the active
conversation for the current `page_context`. If one exists, render its persisted
messages; otherwise render an empty starter state. Do not create a conversation
until the user submits the first turn.

The component sends the current `page_context` with each turn and renders:

- user messages
- assistant text deltas
- progress rows
- tool call rows
- recommendation cards using the existing recommendation operation UI
- authorized navigation actions

When a `recommendation_created` event arrives, the UI should render the same
operation approval/rejection affordances used by the current recommendation
panel. Coach-created recommendation cards must be actionable inside the overlay,
so the user can approve or reject operations without navigating to the workout
screen's recommendation panel.

## Implementation Slices

1. Add `CoachConversation` and `CoachMessage` models.
2. Add coach serializers and read APIs for conversation history.
2a. Add an active-conversation lookup API by page context.
3. Add SSE stream endpoint and event formatting helpers.
4. Add deterministic context builder for workout context.
5. Add `CoachOrchestrator` with structured model output.
6. Add `propose_workout_changes` integration that creates `Recommendation`
   records from `WorkoutPatchDraft`.
7. Add backend-authorized UI action handling.
8. Add frontend coach panel with streamed event rendering.
9. Add training plan and recovery page contexts.
10. Add tests for authorization, context scoping, recommendation creation,
    stale workout behavior, and SSE event order.

## Test Focus

Backend tests should cover:

- conversation creation and reuse by `(user_id, page_type, context_id)`
- users cannot access another user's conversation
- workout context rejects another user's workout
- training plan context cannot create workout patch recommendations
- workout context can create pending `Recommendation` operations
- operation approval still applies through existing recommendation services
- UI navigation actions are rejected for unauthorized entities
- pain/injury input sets safety metadata without creating medical claims
- SSE stream emits key events in order

