# Common API Contract

This document is the shared contract between the React app described in
`docs/app-design.md` and the Django API under `services/api`.

Base URL for all endpoints: `/api/v1`

Unless marked public, endpoints require:

```http
Authorization: Bearer <access_token>
```

Refresh tokens are stored by the API in the `whoop_refresh` HTTP-only cookie.

## Contract Status

### Implemented and aligned

- `POST /users/register/`
- `POST /users/login/`
- `POST /users/token/refresh/`
- `POST /users/logout/`
- `GET /users/me/`
- `PATCH /users/me/`
- `GET /whoop/connect-url/`
- `GET /whoop/callback/`
- `GET /whoop/summary/`
- `POST /whoop/disconnect/`
- `GET /training-plans/`
- `GET /training-plans/:id/`
- `GET /workouts/`
- `GET /workouts/:id/`
- `GET /workout-exercises/`
- `GET /workout-exercises/:id/`
- `POST /recommendations/workouts/:workoutId/generate/`
- `GET /recommendations/:recommendationId/`
- `POST /recommendations/:recommendationId/approve/`
- `POST /recommendations/:recommendationId/reject/`

### Missing for the MVP UI

- A page-ready plan response or default-plan endpoint for the app's first plan
  screen. The design says `GET plans/:id`, but the app does not currently have
  a way to discover which plan ID should be loaded after login.

### Needs refactor or contract decision

- Use `training-plans` as the canonical resource name. The design currently says
  `plans/:id`; the backend exposes `training-plans/:id/`.
- Use `workouts/:id/exercises/` as the canonical exercise list endpoint. The
  design currently says `GET workout/:id`, which conflicts with
  `GET workouts/:id/`.
- Keep recommendation approval and rejection as explicit command endpoints:
  `POST /recommendations/:id/approve/` and
  `POST /recommendations/:id/reject/`. The design currently says
  `PATCH /recommendations/:id` with a status payload.
- Recommendation services currently expect a richer workout snapshot contract
  (`get_workout_snapshot`, `create_workout_snapshot`, `position`,
  `duration_seconds`, `version`, etc.) than the current minimal training API
  exposes (`sets`, `reps`, `time`, `effort`, `note`). The training and
  recommendation domains need to be reconciled before the workout recommendation
  UI is complete.

## Page Flows

### Register page

The register page is public.

1. Call `POST /users/register/`.
2. API returns an auth session and sets the refresh cookie.
3. The React app may either use that returned session directly or call
   `POST /users/login/` with the same credentials.
4. On success, navigate to `/connect-whoop`.

Request:

```json
{
  "email": "athlete@example.com",
  "password": "strong-password",
  "display_name": "Athlete Name"
}
```

Response `201`:

```json
{
  "user": {
    "id": "uuid",
    "email": "athlete@example.com",
    "display_name": "Athlete Name",
    "whoop_user_id": "",
    "created_at": "2026-06-10T00:00:00Z",
    "updated_at": "2026-06-10T00:00:00Z"
  },
  "access": "jwt-access-token",
  "refresh": "jwt-refresh-token"
}
```

### Login page

The login page is public.

1. Call `POST /users/login/`.
2. API returns an auth session and sets the refresh cookie.
3. On success, navigate to `/plan`.

Request:

```json
{
  "email": "athlete@example.com",
  "password": "strong-password"
}
```

Response `200`: same shape as register.

### Connect WHOOP page

Only registration should send a user here automatically.

1. Call `GET /whoop/connect-url/?success_url=<frontend-success-url>`.
2. API creates an OAuth state and returns a WHOOP authorization URL.
3. React redirects the browser to `connect_url`.
4. WHOOP redirects back to `GET /whoop/callback/?code=...&state=...`.
5. API stores the WHOOP connection.
6. API redirects to `WHOOP_FRONTEND_SUCCESS_URL` when configured.
7. React success page refreshes `GET /users/me/` and navigates to `/plan`.

Response `200`:

```json
{
  "state": "oauth-state",
  "connect_url": "https://api.prod.whoop.com/oauth/oauth2/auth?..."
}
```

The `success_url` query parameter is required. It must be an absolute frontend
URL whose origin is allowlisted by the backend.

If WHOOP is down or the API cannot provide a URL, the frontend should show a
temporary-unavailable message and allow the user to continue to `/plan`.

### Plan page

The plan page needs user profile, WHOOP metrics, one selected/default training
plan, and a list of workouts for that plan.

Current backend endpoints:

- `GET /users/me/`
- `GET /whoop/summary/`
- `GET /training-plans/`
- `GET /training-plans/:id/`
- `GET /training-plans/:id/workouts/`
- `GET /workouts/`

Implemented contract:

```http
GET /training-plans/:id/workouts/
```

Response `200`:

```json
[
  {
    "id": "uuid",
    "plan": "uuid",
    "name": "Upper Body",
    "date": "2026-06-10",
    "exercise_count": 5,
    "expected_time": 45
  }
]
```

Refactor decision:

- Either add `GET /training-plans/current/` for the default plan, or have the
  frontend call `GET /training-plans/` and choose the first/current item by
  client rules.
- Add `exercise_count` to the plan-workouts list response so the frontend does
  not need to load every workout's exercises just to render the plan list.

### Workout page

The workout page needs user profile, WHOOP metrics, workout details, workout
exercise rows, and recommendation actions.

Current backend endpoints:

- `GET /users/me/`
- `GET /whoop/summary/`
- `GET /workouts/:id/`
- `GET /workouts/:id/exercises/`
- `GET /workout-exercises/`
- `GET /workout-exercises/:id/`

Implemented contract:

```http
GET /workouts/:id/exercises/
```

Response `200`:

```json
[
  {
    "id": "uuid",
    "workout": "uuid",
    "exercise": {
      "id": "uuid",
      "name": "Bench Press",
      "muscle_group": "Chest"
    },
    "sets": 4,
    "reps": 8,
    "time": 0,
    "effort": "hard",
    "note": ""
  }
]
```

Refactor decision:

- The existing `GET /workout-exercises/` returns all workout exercises for the
  authenticated user. It should either support `?workout=<id>` or be
  complemented by the nested `GET /workouts/:id/exercises/` endpoint.
- The workout exercise response must include enough exercise display data for
  the page. Returning only the exercise ID is not enough for the design.

## Resource Contracts

### User

#### `GET /users/me/`

Response `200`:

```json
{
  "id": "uuid",
  "email": "athlete@example.com",
  "display_name": "Athlete Name",
  "whoop_user_id": "12345",
  "created_at": "2026-06-10T00:00:00Z",
  "updated_at": "2026-06-10T00:00:00Z"
}
```

#### `PATCH /users/me/`

Request:

```json
{
  "display_name": "Updated Name"
}
```

Response `200`: user profile.

### WHOOP summary

#### `GET /whoop/summary/`

Response `200` when connected:

```json
{
  "connected": true,
  "snapshot_date": "2026-06-10",
  "recovery_score": 75,
  "sleep_performance_percent": 88,
  "day_strain": 9.7,
  "hrv_rmssd_milli": 62,
  "resting_heart_rate": 48,
  "sleep_duration_minutes": 430,
  "recent_workout_count": 2,
  "refreshed_at": "2026-06-10T00:00:00Z"
}
```

Response `404` when not connected:

```json
{
  "connected": false,
  "detail": "WHOOP is not connected."
}
```

Frontend should treat this `404` as an unconnected WHOOP state, not a fatal page
error.

### Training plan

Current endpoints:

- `GET /training-plans/`
- `POST /training-plans/`
- `GET /training-plans/:id/`
- `PATCH /training-plans/:id/`
- `PUT /training-plans/:id/`
- `DELETE /training-plans/:id/`

Shape:

```json
{
  "id": "uuid",
  "name": "Summer Block",
  "start_date": "2026-06-01",
  "end_date": "2026-07-01"
}
```

### Workout

Current endpoints:

- `GET /workouts/`
- `POST /workouts/`
- `GET /workouts/:id/`
- `PATCH /workouts/:id/`
- `PUT /workouts/:id/`
- `DELETE /workouts/:id/`

Shape:

```json
{
  "id": "uuid",
  "plan": "uuid",
  "name": "Upper Body",
  "date": "2026-06-10",
  "expected_time": 45
}
```

### Workout exercise

Current endpoints:

- `GET /workout-exercises/`
- `POST /workout-exercises/`
- `GET /workout-exercises/:id/`
- `PATCH /workout-exercises/:id/`
- `PUT /workout-exercises/:id/`
- `DELETE /workout-exercises/:id/`

Current shape:

```json
{
  "id": "uuid",
  "workout": "uuid",
  "exercise": "uuid",
  "sets": 4,
  "reps": 8,
  "time": 15,
  "effort": "hard",
  "note": "Move well."
}
```

MVP page shape should include exercise display data as shown in the Workout page
section.

### Exercise

Current endpoints:

- `GET /exercises/`
- `POST /exercises/`
- `GET /exercises/:id/`
- `PATCH /exercises/:id/`
- `PUT /exercises/:id/`
- `DELETE /exercises/:id/`

Shape:

```json
{
  "id": "uuid",
  "name": "Bench Press",
  "default_sets": 4,
  "default_reps": 8,
  "muscle_group": "Chest",
  "default_time": 0,
  "notes": "Pause reps."
}
```

## Recommendation Contract

Use the implemented command endpoints as the canonical contract.

### Generate recommendation

```http
POST /recommendations/workouts/:workoutId/generate/
```

Request body:

```json
{}
```

The design previously proposed:

```http
POST /recommendations/generate
```

with:

```json
{
  "workoutId": "uuid"
}
```

That should be refactored to the nested workout command endpoint above.

Response `201`:

```json
{
  "id": "uuid",
  "user_id": "uuid",
  "workout_id": "uuid",
  "snapshot_version": "2026-06-10T00:00:00Z",
  "status": "pending",
  "summary": "Adjust today's workout.",
  "reason": "Recovery is lower than usual.",
  "operations": [
    {
      "id": "uuid",
      "sequence": 1,
      "operation_type": "update_exercise",
      "payload": {
        "workout_exercise_id": "uuid",
        "changes": {
          "sets": 3
        },
        "reason": "Reduce volume."
      },
      "display_text": "Update Bench Press: sets to 3"
    }
  ],
  "created_at": "2026-06-10T00:00:00Z",
  "updated_at": "2026-06-10T00:00:00Z"
}
```

Statuses:

- `pending`
- `accepted`
- `rejected`
- `stale`
- `failed`

Operation types:

- `replace_exercise`
- `update_exercise`
- `remove_exercise`
- `add_exercise`

### Get recommendation

```http
GET /recommendations/:recommendationId/
```

Response `200`: recommendation shape.

### Approve recommendation

```http
POST /recommendations/:recommendationId/approve/
```

Request:

```json
{
  "expected_workout_version": "2026-06-10T00:00:00Z"
}
```

Response `200`: recommendation shape with `status: "accepted"`.

Response `409`: workout changed since recommendation generation.

### Reject recommendation

```http
POST /recommendations/:recommendationId/reject/
```

Request:

```json
{}
```

Response `200`: recommendation shape with `status: "rejected"`.

## Backend Refactor Checklist

- Consider adding `?plan=<id>` filtering to `GET /workouts/` for list reuse.
- Consider adding `?workout=<id>` filtering to `GET /workout-exercises/` for
  list reuse alongside the page-specific nested route.
- Add exercise display fields to workout exercise responses.
- Add `exercise_count` to the workout list used by the plan page.
- Decide how the app discovers the active/default plan after login.
- Reconcile recommendation services with the current minimal training models.
  Either restore and expose the richer workout snapshot contract or refactor
  recommendations to use `Workout` and `WorkoutExercise` as they exist now.
- Update `docs/app-design.md` endpoint names to match this contract:
  `training-plans`, `workouts`, nested workout exercise reads, and explicit
  recommendation approve/reject commands.
