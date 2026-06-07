# WHOOP AI Coach - Backend Architecture

## Purpose

This document defines the architectural standards for the WHOOP AI Coach backend.

The application will be built using:

* Python
* Django
* Django REST Framework
* PostgreSQL

The architecture follows:

* Domain-Driven Design (DDD)
* Bounded Contexts
* Service-Oriented Application Layer
* Pragmatic Django

The primary goal is to keep business logic organized, reusable, and easy to evolve while taking advantage of Django's strengths rather than fighting the framework.

---

# Core Principles

## 1. Organize Around Business Capabilities

The primary architectural boundary is the business domain, not technical layers.

Examples:

* Users
* Training
* WHOOP
* Coaching
* AI

Each bounded context owns its data, services, APIs, and integrations.

Example:

```text
training/
whoop/
coaching/
ai/
users/
```

Code should be easy to locate based on business responsibility.

---

## 2. Business Workflows Belong in Services

Complex business workflows should be implemented as application services.

Bad:

```python
class WorkoutView(APIView):

    def post(self, request):
        # 200 lines of business logic
```

Good:

```python
CreateWorkoutService.execute(...)
```

Services provide a consistent entry point that can be reused by:

* REST APIs
* Scheduled jobs
* AI tools
* WHOOP webhooks

---

## 3. Use Django Where It Provides Value

Django is a core part of the platform.

Using:

* Django ORM
* Django authentication
* Django migrations
* Django transactions

is encouraged.

The goal is not to eliminate Django dependencies but to prevent business logic from becoming scattered across views, serializers, models, and infrastructure code.

---

## 4. Keep Domain Rules Centralized

Business rules should exist in one place.

Examples:

* Workout completion rules
* Recommendation approval rules
* Goal validation rules
* Training plan constraints

Avoid duplicating the same rules across:

* Views
* AI prompts
* Scheduled jobs
* Webhook handlers

---

## 5. AI Is a Consumer of Application Services

AI should use the same services as the REST API.

Bad:

```text
AI
 ↓
Database
```

Good:

```text
AI
 ↓
Application Service
 ↓
Database
```

The AI layer orchestrates behavior but does not own business logic.

---

# Bounded Contexts

## Users

Owns:

* Authentication
* User profiles
* User preferences
* WHOOP account association

Example fields:

```text
id
email
display_name
whoop_user_id
created_at
updated_at
```

---

## Training

Owns:

* Exercises
* Workouts
* Training plans
* Goals
* Workout completion

---

## WHOOP

Owns:

* OAuth integration
* Token management
* Webhooks
* WHOOP synchronization
* WHOOP snapshots

---

## Coaching

Owns:

* Recommendations
* Recommendation lifecycle
* User approval workflow
* Recommendation history

---

## AI

Owns:

* Prompt generation
* Tool definitions
* Structured outputs
* Chat conversations

AI does not own business entities.

---

# Project Structure

```text
src/

├── config/
│
├── apps/
│   ├── users/
│   ├── training/
│   ├── whoop/
│   ├── coaching/
│   └── ai/
│
├── shared/
│
└── tests/
```

---

# Context Structure

Each bounded context follows a similar structure.

```text
training/

├── api/
├── services/
├── models/
├── integrations/
├── domain/
└── tests/
```

Not every context requires every folder.

The structure should remain simple and evolve as complexity grows.

---

# Services

Services represent business use cases.

Examples:

## Exercise Services

* CreateExercise
* UpdateExercise
* DeleteExercise
* GetExercise
* SearchExercises

## Goal Services

* CreateGoal
* UpdateGoal
* GetActiveGoal

## Workout Services

* CreateWorkout
* UpdateWorkout
* DeleteWorkout
* GetWorkout
* CompleteWorkout

## Training Plan Services

* CreateTrainingPlan
* UpdateTrainingPlan
* GetTrainingPlan
* DeleteTrainingPlan

Services are the preferred integration point for other contexts.

---

# Persistence

Django models are the primary persistence mechanism.

Example:

```python
class Workout(models.Model):
    ...
```

For simple CRUD operations, using Django ORM directly inside services is acceptable.

Repository abstractions should be introduced only when they provide clear value:

* External data sources
* Complex integrations
* Multiple storage implementations
* Difficult testing scenarios

Avoid creating repositories solely for architectural purity.

---

# API Layer

The API layer contains:

* DRF Views
* Serializers
* Authentication
* Authorization
* Response formatting

Responsibilities:

* Validate requests
* Call services
* Return responses

Business workflows should remain in services.

---

# AI Architecture

AI operates as an orchestration layer.

Example:

```text
Chat
 ↓
GeneratePlanFromGoal
 ↓
CreateTrainingPlanService
 ↓
CreateWorkoutService
```

AI should interact with the system through well-defined services and tools rather than directly manipulating persistence.

---

# Initial Implementation Strategy

Phase 1:

* Users
* Authentication
* Exercises
* Goals
* Workouts
* Training Plans
* WHOOP Synchronization

Phase 2:

* Recommendations
* AI Chat
* Adaptive Planning
* Recovery-Based Modifications

Phase 3:

* Agent Workflows
* Scheduled Coaching
* Long-Term Training Optimization

---

# Architecture Goal

The architecture should allow:

* REST APIs
* AI Agents
* Scheduled Jobs
* WHOOP Webhooks

to use the same business services.

The focus is not strict framework independence but maintaining clear business boundaries, reusable workflows, and a codebase that remains understandable as the product grows.



# Authentication 
- All endpoints will require a JWT with a user ID.
 