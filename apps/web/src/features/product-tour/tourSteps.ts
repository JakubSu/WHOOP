import { type DriveStep } from 'driver.js'

export const EXERCISE_PRACTICE_PROMPT =
  'Replace Dumbbell Lateral Raise with Lean-away Cable Lateral Raise.'

const COACH_COMPOSER_WAIT_MS = 1_500
export type CoachTourActions = {
  openCoach: () => void
  prefillCoachMessage: (message: string) => void
  startFreshConversationAndPrefill: (message: string) => Promise<boolean>
}

export type ProductTourActions = CoachTourActions & {
  goToWeekForTour: () => void
  startGuidedCoachFlow: () => Promise<boolean>
}

type TourStepOptions = {
  hasWhoopConnection: boolean
  isDesktop: boolean
  actions: () => ProductTourActions | null
}

const popover = (title: string, description: string) => ({ title, description })

export function weekNavigationTargetForViewport(isDesktop: boolean) {
  return isDesktop
    ? '[data-tour="week-navigation-desktop"], [data-tour="week-navigation-page"]'
    : '[data-tour="week-navigation-mobile"], [data-tour="week-navigation-page"]'
}

export function createProductTourSteps({
  hasWhoopConnection,
  isDesktop,
  actions,
}: TourStepOptions): DriveStep[] {
  const whoopDescription = hasWhoopConnection
    ? 'Sleep, Recovery, and Strain give your plan the daily context it needs.'
    : 'Connect WHOOP when you are ready to personalize your plan with sleep, recovery, and strain.'
  const weekSteps: DriveStep[] = isDesktop
    ? [{
        element: weekNavigationTargetForViewport(true),
        popover: popover('Your week at a glance', 'Browse scheduled workouts and rest days from the week navigator.'),
      }]
    : [
        {
          onHighlightStarted: () => actions()?.goToWeekForTour(),
          popover: popover('Your week at a glance', 'We are opening the full Week view so you can see every scheduled workout and rest day.'),
        },
        {
          element: '[data-tour="week-navigation-page"]',
          waitForElement: COACH_COMPOSER_WAIT_MS,
          popover: popover('Your week at a glance', 'Browse scheduled workouts and rest days across the full week.'),
        },
      ]

  return [
    {
      popover: popover(
        'Your training, adapted daily',
        'This plan brings your workouts, readiness, and coaching together so training can respond to how you are doing today.',
      ),
    },
    {
      element: '[data-tour="whoop-metrics"]',
      popover: popover('Start with readiness', whoopDescription),
    },
    {
      element: '[data-tour="workout-header"]',
      popover: popover(
        'Today’s workout',
        'Review today’s session here. Use the arrows to move between workouts, or open the workout week for the larger plan.',
      ),
    },
    {
      element: '[data-tour="workout-edit"]',
      popover: popover('You are always in control', 'Edit your workout directly whenever you want. The Coach supports your decisions; it never makes hidden changes.'),
    },
    ...weekSteps,
    {
      onHighlightStarted: () => actions()?.openCoach(),
      popover: popover(
        'Your context-aware Coach',
        'The Coach understands the workout or week you are viewing and can use your available WHOOP context to guide the conversation.',
      ),
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
      onHighlightStarted: () => {
        void actions()?.startGuidedCoachFlow()
      },
      popover: {
        ...popover(
          'Build a workout with the Coach',
          'We have prepared an upper-body workout request for the first rest day in your visible week. Review it, then continue to Send.',
        ),
        onNextClick: (_element, _step, { driver }) => {
          void actions()?.startGuidedCoachFlow().then((ready) => {
            if (ready) driver.moveNext()
          })
        },
      },
    },
    {
      element: '[data-tour="coach-send"]',
      waitForElement: COACH_COMPOSER_WAIT_MS,
      advanceOnClick: true,
      popover: popover('Send your request', 'Click the real Send button to ask the Coach for this workout. The response will stream above.'),
    },
    {
      popover: popover(
        'You are ready to train',
        'Open the Coach whenever you want help. You can replay this tour any time from your profile menu.',
      ),
    },
  ]
}
