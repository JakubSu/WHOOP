import { type DriveStep } from 'driver.js'

export const EXERCISE_PRACTICE_PROMPT =
  'Replace Dumbbell Lateral Raise with Lean-away Cable Lateral Raise.'

const COACH_COMPOSER_WAIT_MS = 1_500
const COACH_RESPONSE_WAIT_MS = 30_000
export const COACH_RECOMMENDATION_CARD_TARGET =
  '[data-tour="coach-recommendation-card"]'
export const COACH_GENERATED_WORKOUT_TARGET =
  '[data-tour="coach-generated-workout-recommendation"]'
export const COACH_REPLACEMENT_RECOMMENDATION_TARGET =
  'article[data-tour="coach-recommendation-message"]:last-of-type [data-tour="coach-replacement-recommendation"]'
export const COACH_REPLACEMENT_ACCEPT_ALL_TARGET =
  'article[data-tour="coach-recommendation-message"]:last-of-type [data-tour="coach-replacement-recommendation"] [data-tour="coach-accept-all"]'
const COACH_CREATE_EXERCISE_TARGET =
  'article:has([data-tour="create-missing-exercise"]):last-of-type [data-tour="create-missing-exercise"]'
export type CoachTourActions = {
  openCoach: () => void
  closeCoach: () => void
  prefillCoachMessage: (message: string) => void
  startFreshConversationAndPrefill: (message: string) => Promise<boolean>
}

export type ProductTourActions = CoachTourActions & {
  notifyGuidedRecommendationExpanded: () => void
  notifyGuidedWorkoutOpened: () => void
  startGuidedCoachFlow: () => Promise<boolean>
}

type TourStepOptions = {
  hasWhoopConnection: boolean
  isDemo: boolean
  isDesktop: boolean
  actions: () => ProductTourActions | null
}

const popover = (title: string, description: string) => ({ title, description })

export function weekNavigationTargetForViewport(isDesktop: boolean) {
  return isDesktop
    ? '[data-tour="week-navigation-desktop"], [data-tour="week-navigation-page"]'
    : '[data-tour="week-navigation-mobile"], [data-tour="week-navigation-page"]'
}

export function whoopMetricsTargetForViewport(isDesktop: boolean) {
  return isDesktop ? '[data-tour="whoop-metrics-desktop"]' : '[data-tour="whoop-metrics-mobile"]'
}

export function createProductTourSteps({
  hasWhoopConnection,
  isDemo,
  isDesktop,
  actions,
}: TourStepOptions): DriveStep[] {
  const whoopDescription = hasWhoopConnection
    ? 'Sleep, Recovery, and Strain give you and your AI coach the context it needs.'
    : 'Connect WHOOP when you are ready to personalize your plan with sleep, recovery, and strain.'
  const weekSteps: DriveStep[] = isDesktop
    ? [{
      element: weekNavigationTargetForViewport(true),
      popover: popover('Your week at a glance', 'Browse scheduled workouts and rest days from the week panel.'),
    }]
    : [
      {
        element: '[data-tour="week-navigation-mobile"]',
        advanceOnClick: true,
        popover: {
          ...popover('Your week at a glance', 'Click the week button to see every scheduled workout and rest day.'),
          showButtons: ['previous', 'close'],
        },
      },
      {
        element: '[data-tour="week-navigation-page"]',
        waitForElement: COACH_COMPOSER_WAIT_MS,
        popover: popover('Your week at a glance', 'Browse scheduled workouts and rest days across the full week.'),
      },
    ]
  const mobileCoachReopenStep: DriveStep[] = isDesktop
    ? []
    : [{
      element: '[data-tour="coach-open"]',
      advanceOnClick: true,
      popover: {
        ...popover('Open your Coach again', 'The workout is open. Click the Coach button to continue with the follow-up request.'),
        showButtons: ['previous', 'close'],
      },
    }]

  const steps: DriveStep[] = [
    {
      popover: popover(
        'Your training, all in one place',
        'Plan your workouts, track your recovery, and use your AI coach to create workouts or recommend changes based on your training.',
      ),
    },
    {
      element: whoopMetricsTargetForViewport(isDesktop),
      popover: popover('Start with readiness', whoopDescription),
    },
    {
      element: '[data-tour="workout-panel"]',
      popover: popover(
        'Today’s workout',
        'Review today’s session here. Use the arrows to move between workouts, or use the week view to browse the full plan.',
      ),
    },
    ...weekSteps,
    isDesktop
      ? {
        element: '[data-tour="coach-panel"]',
        onHighlightStarted: () => actions()?.openCoach(),
        popover: popover(
          'Your context-aware Coach',
          'The Coach understands the workout or week you are viewing and can use your available WHOOP context to guide the conversation.',
        ),
      }
      : {
        element: '[data-tour="coach-open"]',
        advanceOnClick: true,
        popover: {
          ...popover(
            'Your context-aware Coach',
            'Click the Coach button to open a coach that understands the workout or week you are viewing and can use your available WHOOP context to guide the conversation.',
          ),
          showButtons: ['previous', 'close'],
        },
      },
    {
      element: '[data-tour="coach-composer"]',
      waitForElement: COACH_COMPOSER_WAIT_MS,
      popover: popover(
        'Suggestions stay reviewable',
        'Ask for a lighter session, a shorter alternative, or an explanation. Any proposed workout changes remain yours to review and approve.',
      ),
    },
    {
      element: '[data-tour="coach-composer"]',
      waitForElement: COACH_COMPOSER_WAIT_MS,
      onHighlightStarted: () => {
        void actions()?.startGuidedCoachFlow()
      },
      popover: {
        ...popover(
          'Use the example prompt and send it',
          'We prepared an upper-body workout request for tomorrow. Review the prompt, then click Send to continue.',
        ),
        showButtons: ['close'],
      },
    },
    {
      element: '[data-tour="coach-messages"]',
      waitForElement: COACH_RESPONSE_WAIT_MS,
      popover: { ...popover('Wait for the Coach', 'The Coach is preparing your workout. Keep this tour open while the response streams into the conversation.'), showButtons: ['close'] },
    },
    {
      element: COACH_GENERATED_WORKOUT_TARGET,
      waitForElement: COACH_RESPONSE_WAIT_MS,
      onHighlightStarted: () => {
        actions()?.notifyGuidedRecommendationExpanded()
        document
          .querySelector<HTMLElement>(COACH_GENERATED_WORKOUT_TARGET)
          ?.scrollIntoView({ behavior: 'auto', block: 'center' })
      },
      popover: popover('Review the Coach response', 'The generated workout recommendation is open. Review the proposed workout, then click Next.'),
    },
    {
      element: '[data-tour="coach-accept-all"]',
      waitForElement: COACH_RESPONSE_WAIT_MS,
      onHighlighted: () => {
        document
          .querySelector<HTMLElement>('[data-tour="coach-accept-all"]')
          ?.scrollIntoView({ behavior: 'auto', block: 'center' })
      },
      popover: {
        ...popover('Accept the proposed workout', 'Review the proposed workout, then click Accept all to add it to your week.'),
        side: isDesktop ? 'left' as const : 'top' as const,
        showButtons: ['close'],
      },
    },
    {
      element: '[data-tour="workout-panel"]',
      waitForElement: COACH_RESPONSE_WAIT_MS,
      onHighlightStarted: () => {
        if (!isDesktop) actions()?.closeCoach()
        actions()?.notifyGuidedWorkoutOpened()
      },
      popover: popover('Your new workout', 'This is the workout you just accepted. Click Next to continue to the follow-up request.'),
    },
    ...mobileCoachReopenStep,
    {
      element: '[data-tour="coach-composer"]',
      waitForElement: COACH_COMPOSER_WAIT_MS,
      popover: {
        ...popover('Use the follow-up prompt and send it', 'The follow-up prompt is ready. Review it, then click the real Send button to request the replacement exercise.'),
        showButtons: ['close'],
      },
    },
    {
      element: '[data-tour="coach-messages"]',
      waitForElement: COACH_RESPONSE_WAIT_MS,
      popover: { ...popover('Wait for the replacement response', 'The Coach is checking the requested exercise and will explain what to do when it is not in your library.'), showButtons: ['close'] },
    },
    {
      element: COACH_CREATE_EXERCISE_TARGET,
      advanceOnClick: true,
      onHighlightStarted: () => {
        document
          .querySelector<HTMLElement>(COACH_CREATE_EXERCISE_TARGET)
          ?.scrollIntoView({ behavior: 'auto', block: 'center' })
      },
      popover: {
        ...popover('Create a new exercise', 'Click Create new exercise to open the exercise form.'),
        side: 'right' as const,
        showButtons: ['previous', 'close'],
      },
    },
    {
      element: '[data-tour="create-exercise-submit"]',
      popover: { ...popover('Save the exercise', 'Review the pre-filled exercise details, then click Create exercise.'), showButtons: ['close'] },
    },
    {
      element: '[data-tour="coach-messages"]',
      waitForElement: COACH_RESPONSE_WAIT_MS,
      popover: { ...popover('Wait for the replacement workout', 'The Coach is applying your new exercise and preparing an updated recommendation.'), showButtons: ['close'] },
    },
    {
      element: COACH_REPLACEMENT_RECOMMENDATION_TARGET,
      waitForElement: COACH_RESPONSE_WAIT_MS,
      onHighlightStarted: () => {
        document
          .querySelector<HTMLElement>(COACH_REPLACEMENT_RECOMMENDATION_TARGET)
          ?.scrollIntoView({ behavior: 'auto', block: 'center' })
      },
      popover: popover('Review the updated Coach response', 'The updated recommendation includes your new exercise. Review it, then click Next.'),
    },
    {
      element: COACH_REPLACEMENT_ACCEPT_ALL_TARGET,
      waitForElement: COACH_RESPONSE_WAIT_MS,
      onHighlighted: () => {
        document
          .querySelector<HTMLElement>(COACH_REPLACEMENT_ACCEPT_ALL_TARGET)
          ?.scrollIntoView({ behavior: 'auto', block: 'center' })
      },
      popover: { ...popover('Accept the replacement workout', 'Click Accept all to apply the updated recommendation with your new exercise.'), showButtons: ['close'] },
    },
    {
      element: '[data-tour="workout-panel"]',
      waitForElement: COACH_RESPONSE_WAIT_MS,
      onHighlightStarted: () => {
        if (!isDesktop) actions()?.closeCoach()
      },
      popover: popover('Review the updated workout', 'The workout is updated with your new exercise. Review it here before finishing the tour.'),
    },
    {
      element: '[data-tour="workout-edit"]',
      popover: popover('You are always in control', 'Edit your workout directly whenever you want. The Coach supports your decisions; it never makes hidden changes.'),
    },
  ]

  if (isDemo) {
    steps.push({
      popover: {
        ...popover(
          'You’re ready to train!',
          'That’s the full tour. Exit whenever you like, or register to save your training plan and continue with your own account.',
        ),
        nextBtnText: 'Exit tour',
        showButtons: ['next', 'close'],
      },
    })
  }

  return steps
}
