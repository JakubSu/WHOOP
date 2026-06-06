# WHOOP AI Coach

## Overview

WHOOP AI Coach is a web application that uses WHOOP biometric and activity data to adapt a user's training plan and provide personalized coaching recommendations.

The initial target user is the developer. The primary objective is to demonstrate strong AI engineering, product thinking, and software architecture through a working application that integrates WHOOP APIs with LLM-powered decision making.

The project is intended to serve as a portfolio piece for WHOOP engineering leadership and recruiting teams.

---

# Core Problem

Athletes often follow static training plans that do not adapt to daily readiness, recovery, sleep quality, accumulated fatigue, or recent training load.

This application continuously evaluates WHOOP data and adjusts workouts to better align with the athlete's current physiological state.

---

# MVP Scope

## User Story 1 - Adaptive Daily Workout

As a WHOOP user, I want my workout for today to automatically adapt based on my recovery, sleep, cycle/strain, and recent activities.

### Flow

1. User connects WHOOP account.
2. Application retrieves latest WHOOP metrics.
3. Application loads today's planned workout.
4. AI analyzes current readiness.
5. AI recommends modifications.
6. User accepts or rejects changes.
7. Workout is updated.

---

## User Story 2 - AI Coach

As a WHOOP user, I want to discuss my training with an AI coach that understands my goals, training plan, and WHOOP data.

### Flow

1. User opens coach chat.
2. AI receives WHOOP data, training plan, and goals.
3. User asks questions or requests changes.
4. AI provides recommendations.
5. AI may update workouts through approved tools.
6. User accepts modifications.

---

# Architecture

## Frontend

* React
* TypeScript
* Mobile-first responsive design
* Hosted on AWS (S3 + CloudFront)

## Backend

* Python
* Django
* Django REST Framework
* Hosted on AWS App Runner

## Data

* PostgreSQL (RDS)

## AI

* OpenAI API
* Function Calling
* Structured JSON Outputs

## External Integrations

* WHOOP API
* OpenAI API

---

# Core Domain Model

## User

Represents an authenticated athlete.

## TrainingPlan

Represents a collection of planned workouts.

## Workout

Represents a scheduled workout.

## Exercise

Represents an individual exercise within a workout.

## WhoopData

Normalized WHOOP metrics used by the AI system.

## CoachConversation

Stores chat history and coaching interactions.

---

# High-Level Components

## WHOOP Integration Layer

Responsible for:

* Authentication
* WHOOP API communication
* Data normalization

Output:

```json
{
  "recovery": 72,
  "sleep": 84,
  "strain": 13.2,
  "recentActivities": []
}
```

---

## Training Plan Engine

System of record for:

* Training plans
* Workouts
* Exercises

The application owns all training data.

The LLM never directly modifies persistence.

---

## Tool Layer

The boundary between AI and the application.

### Tool 1

```python
get_whoop_data()
```

Returns current WHOOP metrics.

### Tool 2

```python
get_training_plan()
```

Returns current training plan and workout data.

### Tool 3

```python
update_workout()
```

Applies validated workout modifications.

---

## AI Coach Service

Responsible for:

* Prompt construction
* Tool definitions
* OpenAI communication
* Function calling
* Response validation

All AI-related logic lives in this service.

---

## Workout Adaptation Engine

Inputs:

* WHOOP metrics
* User goals
* Current training plan
* Today's workout

Output:

* Workout modifications
* Coaching rationale

This is the primary MVP feature.

---

# AI Strategy

Use structured generation and function calling.

The model never writes directly to the database.

Example output:

```json
{
  "action": "modify_workout",
  "workoutId": "123",
  "changes": {
    "sets": 3,
    "reps": 8,
    "intensity": "moderate"
  },
  "reasoning": "Recovery score is significantly below baseline."
}
```

The backend validates and applies changes through tools.

---

# Build Order

1. Domain model
2. WHOOP integration
3. Training plan engine
4. Tool layer
5. AI coach service
6. Workout adaptation workflow
7. Chat interface
8. Notifications

---

# Explicit Non-Goals (MVP)

* Native iOS application
* Complex multi-agent architecture
* Direct WHOOP Strength Trainer integration
* Advanced calendar management
* Autonomous long-term plan modifications
* RAG/vector databases
* Social features

---

# Success Criteria

A user can:

1. Connect a WHOOP account.
2. Create or import a structured training plan.
3. View WHOOP recovery, sleep, strain, and workout data.
4. Receive AI-generated workout modifications.
5. Accept or reject recommendations.
6. Chat with an AI coach that understands current readiness and training context.
7. Use the application through a publicly accessible deployed URL.
8. Demonstrate the complete workflow in a short product demo.
