import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { driver, type Driver } from 'driver.js'
import 'driver.js/dist/driver.css'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../auth/store/authStore'
import { createProductTourSteps, type CoachTourActions } from './tourSteps'
import { shouldAutoStartProductTour } from './tourEligibility'
import {
  clearProductTourCompletion,
  hasCompletedProductTour,
  markProductTourCompleted,
} from './tourStorage'

const WORKSPACE_READY_INITIAL_DELAY_MS = 250
const WORKSPACE_READY_RETRY_DELAY_MS = 200
const MAX_WORKSPACE_READY_ATTEMPTS = 30
const DRIVER_TARGET_WAIT_MS = 1_000
const NEXT_PAINT_DELAY_MS = 0

type ProductTourContextValue = {
  startTour: () => void
  replayTour: () => void
  registerCoachActions: (actions: CoachTourActions | null) => void
  guidedCoachStage: GuidedCoachStage
  notifyGuidedCoachSubmitted: () => void
  notifyGuidedCoachCompleted: (hasExerciseResolution: boolean) => void
  notifyGuidedExerciseResolutionStarted: () => void
}

export type GuidedCoachStage = null | 'initial_ready' | 'waiting_initial' | 'followup_ready' | 'waiting_followup' | 'exercise_resolution' | 'waiting_resolution' | 'complete' | 'unavailable'

const ProductTourContext = createContext<ProductTourContextValue | null>(null)

export function ProductTourProvider({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const status = useAuthStore((state) => state.status)
  const coachActionsRef = useRef<CoachTourActions | null>(null)
  const driverRef = useRef<Driver | null>(null)
  const autoStartAttemptedRef = useRef<string | null>(null)
  const [guidedCoachStage, setGuidedCoachStage] = useState<GuidedCoachStage>(null)

  const completeTour = useCallback(() => {
    if (user) markProductTourCompleted(user.id)
  }, [user])

  const startTour = useCallback(() => {
    if (!user || driverRef.current?.isActive()) return

    const hasWhoopConnection = Boolean(user.whoop_user_id)
    const tour = driver({
      steps: createProductTourSteps({
        hasWhoopConnection,
        isDesktop: window.matchMedia('(min-width: 1024px)').matches,
        actions: () => coachActionsRef.current ? ({
          ...coachActionsRef.current,
          goToWeekForTour: () => {
            const date = document.querySelector<HTMLElement>('[data-tour-workout-date]')?.dataset.tourWorkoutDate
            if (date) navigate(`/week?date=${encodeURIComponent(date)}`)
          },
          startGuidedCoachFlow: async () => {
            const restDate = document.querySelector<HTMLElement>('[data-tour-rest-day]')?.dataset.tourRestDay
            const action = coachActionsRef.current
            if (!restDate || !action) {
              setGuidedCoachStage('unavailable')
              return
            }
            const prompt = `Create a 45-minute upper-body workout for ${restDate} using Bench Press, Arnold Press, Dumbbell Curl, and Dumbbell Lateral Raise.`
            const ready = await action.startFreshConversationAndPrefill(prompt)
            setGuidedCoachStage(ready ? 'initial_ready' : 'unavailable')
            if (ready) {
              completeTour()
              driverRef.current?.destroy()
            }
          },
        }) : null,
      }),
      animate: !window.matchMedia('(prefers-reduced-motion: reduce)').matches,
      smoothScroll: true,
      allowClose: true,
      allowKeyboardControl: true,
      showButtons: ['previous', 'next', 'close'],
      showProgress: true,
      progressText: '{{current}} of {{total}}',
      nextBtnText: 'Next',
      prevBtnText: 'Back',
      doneBtnText: 'Finish',
      popoverClass: 'whoop-product-tour',
      stagePadding: 8,
      stageRadius: 10,
      skipMissingElement: true,
      waitForElement: DRIVER_TARGET_WAIT_MS,
      onCloseClick: () => {
        completeTour()
        tour.destroy()
      },
      onDoneClick: () => {
        completeTour()
        tour.destroy()
      },
      onDestroyed: () => {
        driverRef.current = null
      },
    })
    driverRef.current = tour
    tour.drive()
  }, [completeTour, navigate, user])

  const replayTour = useCallback(() => {
    if (!user) return
    clearProductTourCompletion(user.id)
    driverRef.current?.destroy()
    if (!location.pathname.startsWith('/workouts/')) {
      autoStartAttemptedRef.current = null
      navigate('/')
      return
    }
    autoStartAttemptedRef.current = user.id
    window.setTimeout(startTour, NEXT_PAINT_DELAY_MS)
  }, [location.pathname, navigate, startTour, user])

  const registerCoachActions = useCallback((actions: CoachTourActions | null) => {
    coachActionsRef.current = actions
  }, [])

  useEffect(() => {
    if (status !== 'authenticated' || !user || hasCompletedProductTour(user.id)) return
    if (autoStartAttemptedRef.current === user.id) return
    if (!location.pathname.startsWith('/workouts/')) return

    let attempts = 0
    const startWhenWorkspaceReady = () => {
      attempts += 1
      const workspaceReady = Boolean(document.querySelector('[data-tour-workspace-ready="true"]'))
      if (shouldAutoStartProductTour({
        isAuthenticated: status === 'authenticated',
        hasUser: Boolean(user),
        hasCompleted: hasCompletedProductTour(user.id),
        workspaceReady,
        hasAutoStarted: autoStartAttemptedRef.current === user.id,
      })) {
        autoStartAttemptedRef.current = user.id
        startTour()
        return
      }
      if (attempts < MAX_WORKSPACE_READY_ATTEMPTS) {
        window.setTimeout(startWhenWorkspaceReady, WORKSPACE_READY_RETRY_DELAY_MS)
      }
    }
    const timeout = window.setTimeout(startWhenWorkspaceReady, WORKSPACE_READY_INITIAL_DELAY_MS)
    return () => window.clearTimeout(timeout)
  }, [location.pathname, startTour, status, user])

  return (
    <ProductTourContext.Provider value={{ startTour, replayTour, registerCoachActions, guidedCoachStage,
      notifyGuidedCoachSubmitted: () => setGuidedCoachStage((stage) => stage === 'initial_ready' ? 'waiting_initial' : stage === 'followup_ready' ? 'waiting_followup' : stage),
      notifyGuidedCoachCompleted: (hasExerciseResolution) => setGuidedCoachStage((stage) => stage === 'waiting_initial' ? 'followup_ready' : stage === 'waiting_followup' ? hasExerciseResolution ? 'exercise_resolution' : 'unavailable' : stage === 'waiting_resolution' ? 'complete' : stage),
      notifyGuidedExerciseResolutionStarted: () => setGuidedCoachStage((stage) => stage === 'exercise_resolution' ? 'waiting_resolution' : stage),
    }}>
      {children}
    </ProductTourContext.Provider>
  )
}

export function useProductTour() {
  const value = useContext(ProductTourContext)
  if (!value) throw new Error('useProductTour must be used within ProductTourProvider')
  return value
}
