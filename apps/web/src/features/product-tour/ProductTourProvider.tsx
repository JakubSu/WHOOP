import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef, useState } from 'react'
import { driver, type Driver } from 'driver.js'
import 'driver.js/dist/driver.css'
import { useLocation, useNavigate } from 'react-router-dom'
import { useAuthStore } from '../auth/store/authStore'
import { COACH_GENERATED_WORKOUT_TARGET, createProductTourSteps, type CoachTourActions } from './tourSteps'
import { shouldAutoStartProductTour } from './tourEligibility'
import { addDaysIso, getLocalDateIso } from '../training/services/formatters'
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
  notifyGuidedRecommendationExpanded: () => void
  notifyGuidedRecommendationAccepted: () => void
  notifyGuidedWorkoutOpened: () => void
}

export type GuidedCoachStage = null | 'initial_ready' | 'waiting_initial' | 'review_initial' | 'waiting_initial_accept' | 'week_ready' | 'followup_ready' | 'waiting_followup' | 'exercise_resolution' | 'waiting_resolution' | 'review_replacement' | 'updated_workout' | 'complete' | 'unavailable'

const ProductTourContext = createContext<ProductTourContextValue | null>(null)

export function ProductTourProvider({ children }: { children: ReactNode }) {
  const location = useLocation()
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const status = useAuthStore((state) => state.status)
  const coachActionsRef = useRef<CoachTourActions | null>(null)
  const driverRef = useRef<Driver | null>(null)
  const autoStartAttemptedRef = useRef<string | null>(null)
  const guidedCoachStartRef = useRef<Promise<boolean> | null>(null)
  const guidedWorkoutDateRef = useRef<string | null>(null)
  const [guidedCoachStage, setGuidedCoachStage] = useState<GuidedCoachStage>(null)
  const previousGuidedCoachStageRef = useRef<GuidedCoachStage>(null)

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
            const date = guidedWorkoutDateRef.current ?? document.querySelector<HTMLElement>('[data-tour-workout-date]')?.dataset.tourWorkoutDate
            if (date) navigate(`/week?date=${encodeURIComponent(date)}`)
          },
          notifyGuidedRecommendationExpanded: () => setGuidedCoachStage((stage) => stage === 'review_initial' ? 'waiting_initial_accept' : stage),
          notifyGuidedWorkoutOpened: () => setGuidedCoachStage((stage) => stage === 'week_ready' ? 'followup_ready' : stage),
          startGuidedCoachFlow: () => {
            if (guidedCoachStartRef.current) return guidedCoachStartRef.current
            const start = async () => {
            const action = coachActionsRef.current
            if (!action) {
              setGuidedCoachStage('unavailable')
              return false
            }
            const tomorrow = addDaysIso(getLocalDateIso(), 1)
            guidedWorkoutDateRef.current = tomorrow
            const prompt = `Create a 45-minute upper-body workout for ${tomorrow} using Bench Press, Arnold Press, Dumbbell Curl, and Dumbbell Lateral Raise.`
            const ready = await action.startFreshConversationAndPrefill(prompt)
            setGuidedCoachStage(ready ? 'initial_ready' : 'unavailable')
            return ready
            }
            guidedCoachStartRef.current = start()
            return guidedCoachStartRef.current
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
    guidedCoachStartRef.current = null
    guidedWorkoutDateRef.current = null
    previousGuidedCoachStageRef.current = null
    setGuidedCoachStage(null)
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

  const notifyGuidedRecommendationExpanded = useCallback(() => {
    const tour = driverRef.current
    if (
      !tour?.isActive() ||
      guidedCoachStage !== 'review_initial' ||
      tour.getActiveStep()?.element !== COACH_GENERATED_WORKOUT_TARGET
    ) {
      return
    }

    setGuidedCoachStage('waiting_initial_accept')
    window.requestAnimationFrame(() => {
      const target = document.querySelector<HTMLElement>(COACH_GENERATED_WORKOUT_TARGET)
      target?.scrollIntoView({ behavior: 'auto', block: 'center' })
      if (driverRef.current?.isActive()) driverRef.current.refresh()
    })
  }, [guidedCoachStage])

  useEffect(() => {
    const previousStage = previousGuidedCoachStageRef.current
    previousGuidedCoachStageRef.current = guidedCoachStage
    const shouldAdvance =
      (previousStage === 'initial_ready' && guidedCoachStage === 'waiting_initial') ||
      (previousStage === 'waiting_initial' && guidedCoachStage === 'review_initial') ||
      (previousStage === 'waiting_initial_accept' && guidedCoachStage === 'week_ready') ||
      (previousStage === 'followup_ready' && guidedCoachStage === 'waiting_followup') ||
      (previousStage === 'waiting_followup' && guidedCoachStage === 'exercise_resolution') ||
      (previousStage === 'exercise_resolution' && guidedCoachStage === 'waiting_resolution') ||
      (previousStage === 'waiting_resolution' && guidedCoachStage === 'review_replacement') ||
      (previousStage === 'review_replacement' && guidedCoachStage === 'updated_workout')
    if (!shouldAdvance || !driverRef.current?.isActive()) return
    if (guidedCoachStage === 'week_ready') {
      const date = guidedWorkoutDateRef.current
      if (date) navigate(`/week?date=${encodeURIComponent(date)}`)
    }
    let attempts = 0
    const moveNextWhenReady = () => {
      const tour = driverRef.current
      if (!tour?.isActive()) return
      if (guidedCoachStage === 'week_ready' && !window.location.pathname.startsWith('/week')) {
        const date = guidedWorkoutDateRef.current
        if (date) navigate(`/week?date=${encodeURIComponent(date)}`)
        window.setTimeout(moveNextWhenReady, WORKSPACE_READY_RETRY_DELAY_MS)
        return
      }
      const nextElement = tour.getNextStep()?.element
      const nextSelector = typeof nextElement === 'string' ? nextElement : null
      if (
        nextSelector &&
        !document.querySelector(nextSelector) &&
        attempts < MAX_WORKSPACE_READY_ATTEMPTS
      ) {
        attempts += 1
        window.setTimeout(moveNextWhenReady, WORKSPACE_READY_RETRY_DELAY_MS)
        return
      }
      tour.moveNext()
    }
    window.setTimeout(moveNextWhenReady, NEXT_PAINT_DELAY_MS)
  }, [guidedCoachStage])

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
      notifyGuidedCoachCompleted: (hasExerciseResolution) => setGuidedCoachStage((stage) => stage === 'waiting_initial' ? 'review_initial' : stage === 'waiting_followup' ? hasExerciseResolution ? 'exercise_resolution' : 'unavailable' : stage === 'waiting_resolution' ? 'review_replacement' : stage),
      notifyGuidedExerciseResolutionStarted: () => setGuidedCoachStage((stage) => stage === 'exercise_resolution' ? 'waiting_resolution' : stage),
      notifyGuidedRecommendationExpanded,
      notifyGuidedRecommendationAccepted: () => setGuidedCoachStage((stage) => stage === 'waiting_initial_accept' ? 'week_ready' : stage === 'review_replacement' ? 'updated_workout' : stage),
      notifyGuidedWorkoutOpened: () => setGuidedCoachStage((stage) => stage === 'week_ready' ? 'followup_ready' : stage),
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
