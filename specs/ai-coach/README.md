# AI Coach Bruno Collection

This collection covers every endpoint currently exposed by the Django API under
`/api/v1`.

## Environment

Use the `Local` environment and set:

- `baseUrl`: API root, default `http://localhost:8000/api/v1`
- `accessToken`: JWT access token returned by login/register/refresh
- `refreshToken`: refresh token returned by login/register/refresh, if you are
  not using the HTTP-only cookie
- ID variables such as `trainingPlanId`, `workoutId`, `exerciseId`,
  `workoutExerciseId`, `recommendationId`, and `recommendationOperationId`
- `frontendSuccessUrl`: frontend URL to redirect back to after WHOOP OAuth,
  default `http://localhost:5173/connect-whoop/success`

Collection-level auth is configured as bearer auth using `{{accessToken}}`.
Public auth endpoints override that with `auth: none`.

## Suggested Flow

1. Run `Auth/Register` or `Auth/Login`.
2. The post-response script stores `access`, `refresh`, and `user.id` into the
   active environment.
3. Run `Auth/Refresh Token` when needed. Its post-response script updates both
   `accessToken` and `refreshToken`.
4. Run `Recommendations/Generate Recommendation` or `Recommendations/Get Recommendation`
   to store the latest `recommendationId` and `recommendationOperationId`.
5. Copy any other created resource IDs into the matching environment variables.
6. Set `frontendSuccessUrl` before running `WHOOP/Get Connect URL`.
7. Run the protected requests. They inherit bearer authorization from the
   collection.
