Start with one complete vertical slice:

> User asks to modify one workout → coach retrieves it → creates a pending proposal → user approves it → workout changes.

Do not start with streaming, long-term memory, WHOOP retrieval, or every possible coach tool.

## Phase 1: Define the workout-change contract

Create framework-independent Pydantic models:

```text
coaching/
├── domain/
│   ├── change.py
│   ├── proposal.py
│   └── errors.py
```

Define:

```python
class ExerciseChange(BaseModel):
    operation: Literal["add", "remove", "replace", "update"]
    workout_exercise_id: UUID | None = None
    exercise_id: UUID | None = None
    replacement_exercise_id: UUID | None = None
    sets: int | None = Field(default=None, ge=1, le=20)
    reps: int | None = Field(default=None, ge=1, le=100)
    reason: str


class ProposeWorkoutChangeCommand(BaseModel):
    workout_id: UUID
    expected_version: int
    summary: str
    changes: list[ExerciseChange]
```

Prefer identifying an existing item with `workout_exercise_id`. An `exercise_id` alone can be ambiguous if the same exercise occurs twice.

Tests:

- Reject unsupported operation.
- Reject zero or negative sets/reps.
- Require `workout_exercise_id` for remove/update/replace.
- Require `exercise_id` for add.
- Require `replacement_exercise_id` for replace.
- Reject empty changes.
- Reject excessive numbers of changes.
- Accept one valid example of every operation.

These rules should use Pydantic validators where they describe input shape.

## Phase 2: Implement deterministic proposal creation

Create the application service before involving an LLM:

```text
coaching/
├── application/
│   ├── propose_workout_change.py
│   ├── approve_workout_change.py
│   └── reject_workout_change.py
├── domain/
│   ├── ports.py
│   └── proposal.py
└── infrastructure/
    ├── django_models.py
    └── repositories.py
```

`ProposeWorkoutChange` should:

1. Load the workout for the authenticated user.
2. Reject access if the workout is not owned by that user.
3. Compare the workout version with `expected_version`.
4. Apply the requested changes to an in-memory copy.
5. Validate the resulting workout through the training domain.
6. Calculate a before/after diff.
7. Save a `WorkoutChangeProposal` with `pending` status.
8. Return the proposal ID and diff.
9. Leave the actual workout unchanged.

Tests:

- Creates a pending proposal for valid input.
- Does not update the workout.
- Rejects another user’s workout.
- Rejects a nonexistent workout.
- Rejects a stale version.
- Rejects a nonexistent exercise.
- Rejects invalid resulting workout state.
- Produces the correct before/after diff.
- Does not persist anything when validation fails.
- Saves the authenticated `user_id` and conversation ID.
- Handles duplicate proposal requests according to an explicit policy.

Use fake repositories in unit tests. These tests should not need Django, PostgreSQL, Pydantic AI, or OpenAI.

## Phase 3: Implement approval and rejection

Approval is a normal application operation, not an agent tool.

`ApproveWorkoutChange` should:

1. Load the proposal for the authenticated user.
2. Confirm its status is `pending`.
3. Load the current workout.
4. Recheck the base workout version.
5. Revalidate the proposed result.
6. Update the workout inside a database transaction.
7. Increment its version.
8. Mark the proposal `approved`.

Tests:

- Approval applies the exact proposed result.
- Approval increments the workout version.
- Approval marks the proposal approved.
- Rejection leaves the workout unchanged.
- A rejected proposal cannot be approved.
- An approved proposal cannot be applied twice.
- Another user cannot approve or reject it.
- A stale proposal cannot overwrite a newer workout.
- Failure rolls back both workout and proposal updates.
- Two concurrent approval attempts result in only one update.

The last two should be PostgreSQL integration tests because in-memory repositories cannot prove transaction or locking behavior.

## Phase 4: Add the REST API

Implement:

```text
POST /api/workout-change-proposals/{id}/approve
POST /api/workout-change-proposals/{id}/reject
GET  /api/workout-change-proposals/{id}
```

Keep proposal creation internal initially because the agent tool will call the application service directly.

API tests:

- Unauthenticated requests return `401`.
- Wrong-owner requests return `404` or `403`, following one consistent policy.
- Successful approval returns the updated workout.
- Stale proposal returns `409 Conflict`.
- Invalid proposal state returns `409 Conflict`.
- Repeated approval is idempotent or returns a documented conflict.
- Response includes a frontend-renderable diff.
- Database state matches the response.

At this point, verify the entire workflow manually without AI by creating a proposal through a test fixture or temporary development endpoint.

## Phase 5: Add the Pydantic AI dependencies

```python
@dataclass
class CoachDependencies:
    user_id: UUID
    conversation_id: UUID
    training_queries: TrainingQueries
    recovery_queries: RecoveryQueries
    proposal_service: ProposeWorkoutChange
```

Dependencies must contain trusted runtime state. The model must never provide `user_id`.

Tests:

- Dependencies use the authenticated request user.
- A model-supplied user ID cannot override the authenticated user.
- Services are provided explicitly and can be replaced with fakes.
- Each run receives the correct conversation ID.

## Phase 6: Implement read tools first

Start with only:

```text
get_workout(workout_id)
get_workout_for_date(date)
get_training_plan(date_from, date_to)
get_recovery_summary(date)
```

Every tool should call an application query service rather than Django ORM directly.

Tests for every tool:

- Returns only the authenticated user’s data.
- Rejects inaccessible IDs.
- Validates dates and bounded date ranges.
- Returns a deliberately limited response schema.
- Handles missing recovery data explicitly.
- Does not leak internal database fields.
- Converts application errors into useful tool responses.
- Times out or fails predictably when its dependency fails.

These tests should call the Python tool function directly with fake dependencies.

## Phase 7: Add the proposal tool

```python
@coach_agent.tool
async def propose_workout_change(
    ctx: RunContext[CoachDependencies],
    proposal: ProposeWorkoutChangeCommand,
) -> WorkoutChangeProposalResult:
    return await ctx.deps.proposal_service.execute(
        user_id=ctx.deps.user_id,
        conversation_id=ctx.deps.conversation_id,
        command=proposal,
    )
```

This adapter should remain thin. Business validation stays in `ProposeWorkoutChange`.

Tests:

- Passes the authenticated user from dependencies.
- Passes the correct conversation ID.
- Returns the persisted proposal ID and deterministic diff.
- Cannot directly update a workout.
- Propagates stale-version and authorization failures safely.
- Rejects malformed model-generated arguments before executing the service.
- Does not expose an approval capability.

## Phase 8: Create the minimal coach agent

Add:

```text
ai/
├── application/
│   └── run_coach.py
├── domain/
│   ├── dependencies.py
│   └── outputs.py
└── infrastructure/
    └── pydantic_ai/
        ├── coach_agent.py
        ├── instructions.py
        └── tools.py
```

Initial instructions should require the agent to:

- Retrieve authoritative workout data before proposing changes.
- Use recovery data when the request depends on readiness.
- Create proposals instead of claiming to apply changes.
- State when recovery data is missing or stale.
- Ask for clarification when the target workout is ambiguous.
- Avoid medical diagnosis.

Agent tests using Pydantic AI test models:

- “Make tomorrow easier” retrieves tomorrow’s workout.
- A recovery-dependent request retrieves recovery data.
- A modification request calls the proposal tool.
- A question about the workout uses read tools without proposing changes.
- An ambiguous date causes clarification rather than guessing.
- The final message calls the change pending-not applied.
- Missing recovery data is disclosed.
- The agent never calls tools belonging to another user.
- Tool failure produces a safe response.
- Maximum request/tool-call limits stop loops.

Do not assert exact prose. Assert tool calls, arguments, proposal properties and important semantic facts.

## Phase 9: Persist conversations

Add:

```text
CoachConversation
CoachMessage
AgentRun
```

For each run:

1. Authorize the conversation.
2. Load a bounded amount of message history.
3. Run the agent.
4. Save the user message.
5. Save the returned model messages.
6. Save run metadata and any proposal relationship.

Tests:

- Messages retain their correct order and roles.
- Conversation ownership is enforced.
- A failed run does not create a fake successful assistant message.
- Tool-call/tool-result messages survive serialization.
- History from one user cannot enter another user’s run.
- Long conversations use an explicit truncation or summarization policy.
- Current workout data is retrieved again rather than trusted from history.

## Phase 10: Add the non-streaming chat endpoint

Implement non-streaming first:

```text
POST /api/coach/conversations/{id}/messages
```

Example response:

```json
{
  "message": "I created a lower-intensity version for your review.",
  "proposal": {
    "id": "…",
    "status": "pending",
    "diff": {}
  }
}
```

Render the proposal card from persisted proposal data, not model-written JSON.

End-to-end tests:

1. Authenticate as a user.
2. Create a training plan and workout.
3. Submit a coach message.
4. Confirm a pending proposal exists.
5. Confirm the workout is unchanged.
6. Approve the proposal.
7. Confirm the expected workout update.
8. Submit approval again.
9. Confirm no duplicate modification occurs.

Also test rejection, wrong ownership and stale workout versions.

## Phase 11: Integrate WHOOP recovery

Keep the agent dependent on a normalized `RecoveryQueries` interface. The coach should not call the external WHOOP API directly.

Test:

- Fresh recovery is returned.
- Missing recovery is represented explicitly.
- Stale recovery includes its timestamp.
- WHOOP failure does not prevent unrelated workout questions.
- Recovery belonging to another user is inaccessible.
- External WHOOP payload changes do not affect the coach’s normalized contract.

## Phase 12: Add streaming last

Once the non-streaming flow works, introduce SSE events:

```text
message_started
text_delta
tool_started
tool_completed
proposal_created
message_completed
error
```

Streaming tests:

- Events have stable schemas.
- Text deltas arrive in order.
- `proposal_created` contains the saved proposal ID.
- Disconnecting does not apply a proposal.
- Tool failure emits an error and terminates cleanly.
- The final message is persisted once.
- Reconnection does not duplicate side effects.

## First milestone

Stop after Phase 4 and verify:

> A proposed workout change can be created, previewed, approved and rejected entirely without an LLM.

Then complete Phases 5–10 and verify:

> Given “My recovery is low; make tomorrow easier,” the coach retrieves the correct recovery and workout, saves a valid pending proposal, shows an accurate diff, and cannot modify the workout before authenticated approval.

That sequence isolates the risky part-the state-changing workflow-and makes Pydantic AI a replaceable orchestration layer instead of the foundation of your business logic.
