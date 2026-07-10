# Context

## Glossary

### Training Plan
A named schedule of planned workouts for a single user across a date range.
Each user may have at most one training plan.
Its planned workouts are presented in ascending calendar order from oldest to newest.

### Planned Workout
A workout that belongs to a training plan and is scheduled for exactly one calendar date.

### Ad-hoc Workout
A workout that does not belong to a training plan and may be unscheduled.

### Today's Workout
The planned workout scheduled for the current local date for a user.

### Workout Landing Screen
The first training screen shown after login.
It shows Today's Workout when a planned workout exists for the current local date.
Otherwise it shows the closest upcoming planned workout and a header stating that no workout is scheduled today.

### Workout Screen Title
On the workout detail screen, the primary title is `Today` when the workout is scheduled for the current local date.
Otherwise the primary title is the formatted workout date.
The secondary title is always the workout name.
