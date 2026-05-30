# WHOOP AI Workout Planner

Personal project exploring how WHOOP recovery data and generative AI can be used to build a smarter workout planner and tracker.

## Overview

The goal of this project is to create a fitness planning assistant that recommends workouts based on a user's current readiness, recent training load, sleep, recovery, and strain. Instead of following a static workout plan, the app should adapt day by day using WHOOP data and a personalized bank of favorite exercises.

At a high level, the system will:

- Pull health and performance data from the WHOOP API.
- Track favorite exercises, workout preferences, and training goals.
- Recommend workouts based on recovery, sleep, strain, and recent activity.
- Use generative AI to explain recommendations and adjust plans conversationally.
- Help track completed workouts and compare planned effort against actual strain.

## Core Idea

Most workout plans assume every day is the same. This project starts from the opposite assumption: training should respond to how the body is doing today.

For example:

- High recovery, good sleep, and low recent strain may suggest a harder strength or conditioning session.
- Low recovery or poor sleep may suggest mobility, technique work, zone 2 cardio, or rest.
- High accumulated strain may shift recommendations toward recovery-focused work.
- A user's preferred exercises should shape the actual workout instead of producing generic recommendations.

## Planned Features

### WHOOP Data Integration

- OAuth connection to WHOOP.
- Fetch daily recovery, sleep, strain, and workout data.
- Normalize WHOOP metrics into a format the recommendation engine can use.
- Store historical data for trend-aware planning.

### Exercise Bank

- Maintain a personal library of favorite exercises.
- Track exercise type, muscle groups, equipment, intensity, and constraints.
- Support categories such as strength, cardio, mobility, conditioning, and recovery.
- Allow preferred and avoided exercises to shape recommendations.

### Workout Recommendations

- Generate workout suggestions based on:
  - Sleep quality
  - Recovery score
  - Day strain
  - Recent workouts
  - Training goals
  - Available time
  - Favorite exercises
- Recommend intensity, volume, and exercise selection.
- Offer alternatives when the user wants something easier, harder, shorter, or equipment-specific.

### Generative AI Layer

- Explain why a workout was recommended.
- Let the user ask for modifications in natural language.
- Generate structured workout plans from available exercises.
- Summarize weekly progress and readiness trends.
- Suggest adjustments based on consistency, recovery, and strain patterns.

### Workout Tracking

- Log planned workouts.
- Mark workouts as completed, skipped, or modified.
- Compare intended intensity against WHOOP strain after completion.
- Use completed workout history to improve future recommendations.

## Example Recommendation Flow

1. User opens the app.
2. App fetches latest WHOOP recovery, sleep, and strain data.
3. Recommendation engine evaluates readiness and recent training load.
4. Exercise bank filters possible workouts based on user preferences and constraints.
5. AI generates a workout recommendation with a short explanation.
6. User accepts, edits, or asks for an alternative.
7. Completed workout is saved and later compared with WHOOP strain data.

## Possible Tech Stack

This is still open, but likely options include:

- Backend: Python, FastAPI, or Node.js
- Frontend: React, Next.js, or a mobile-first web app
- Database: PostgreSQL or SQLite for early prototyping
- AI: OpenAI API for workout generation, summarization, and conversational edits
- Data source: WHOOP API

## WHOOP API Collection

The WHOOP OpenAPI spec and Bruno collection are stored under `specs/WHOOP API`.

To use the collection:

1. Create an app in the WHOOP Developer Dashboard.
2. Add your redirect URI in the WHOOP Developer Dashboard.
3. Open the `PROD` Bruno environment.
4. Set `oauth_client_id`, `oauth_client_secret`, and `oauth_callback_url`.
5. Use OAuth 2.0 to fetch an access token.

The collection is configured for WHOOP's OAuth 2.0 authorization code flow:

- Authorization URL: `https://api.prod.whoop.com/oauth/oauth2/auth`
- Token URL: `https://api.prod.whoop.com/oauth/oauth2/token`
- Client authentication: send client credentials in the request body
- Scopes: `read:recovery read:cycles read:workout read:sleep read:profile read:body_measurement offline`

The `offline` scope is included so the app can receive a refresh token for longer-running personal tracking workflows.

## Early Roadmap

1. Define data model for users, exercises, workouts, and WHOOP metrics.
2. Build WHOOP OAuth integration.
3. Create an initial exercise bank.
4. Implement a rule-based recommendation engine.
5. Add AI-generated explanations and workout formatting.
6. Build workout logging and history views.
7. Add weekly summaries and adaptive planning.
8. Refine recommendations based on completed workouts and strain feedback.

## Open Questions

- Should this start as a web app, mobile app, or CLI prototype?
- How much should recommendations be rule-based versus AI-generated?
- What training goals should be supported first: strength, hypertrophy, endurance, general fitness, or recovery?
- Should the app recommend full workouts, weekly plans, or both?
- How should the system handle injuries, soreness, and subjective readiness?

## Status

This project is in the idea and planning stage.
