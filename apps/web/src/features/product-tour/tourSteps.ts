import { type DriveStep } from 'driver.js'

export const EXERCISE_PRACTICE_PROMPT =
  'Replace barbell rows with chest-supported dumbbell rows.'

const COACH_COMPOSER_WAIT_MS = 1_500
const NEXT_PAINT_DELAY_MS = 0

export type ProductTourActions = {
  openCoach: () => void
  prefillCoachMessage: (message: string) => void
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
      element: weekNavigationTargetForViewport(isDesktop),
      popover: popover(
        'Your week at a glance',
        'Browse scheduled workouts and rest days to see how your training is laid out across the week.',
      ),
    },
    {
      element: '[data-tour="workout-edit"]',
      popover: {
        ...popover(
          'You are always in control',
          'Edit your workout directly whenever you want. The Coach supports your decisions; it never makes hidden changes.',
        ),
        onNextClick: (_element, _step, { driver }) => {
          actions()?.openCoach()
          window.setTimeout(() => driver.moveNext(), NEXT_PAINT_DELAY_MS)
        },
      },
    },
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
      popover: {
        ...popover(
          'Need an exercise that is not in your library?',
          'The Coach can help you create it or choose an existing match. Try the optional example below; it only fills the message, and will not send anything.',
        ),
        onPopoverRender: (popoverDom) => {
          const button = document.createElement('button')
          button.type = 'button'
          button.className = 'product-tour-practice-button'
          button.textContent = 'Prefill example'
          button.addEventListener('click', () => {
            actions()?.prefillCoachMessage(EXERCISE_PRACTICE_PROMPT)
          })
          popoverDom.footer.prepend(button)
        },
      },
    },
    {
      popover: popover(
        'You are ready to train',
        'Open the Coach whenever you want help. You can replay this tour any time from your profile menu.',
      ),
    },
  ]
}
