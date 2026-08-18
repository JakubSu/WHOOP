import { createContext, type ReactNode, useCallback, useContext, useEffect, useRef } from 'react'
import { driver, type Driver } from 'driver.js'
import 'driver.js/dist/driver.css'
import { useLocation } from 'react-router-dom'
import { useAuthStore } from '../auth/store/authStore'
import { createProductTourSteps, type ProductTourActions } from './tourSteps'
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
  registerCoachActions: (actions: ProductTourActions | null) => void
}

const ProductTourContext = createContext<ProductTourContextValue | null>(null)

export function ProductTourProvider({ children }: { children: ReactNode }) {
  const location = useLocation()
  const user = useAuthStore((state) => state.user)
  const status = useAuthStore((state) => state.status)
  const coachActionsRef = useRef<ProductTourActions | null>(null)
  const driverRef = useRef<Driver | null>(null)
  const autoStartAttemptedRef = useRef<string | null>(null)

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
        actions: () => coachActionsRef.current,
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
  }, [completeTour, user])

  const replayTour = useCallback(() => {
    if (!user) return
    clearProductTourCompletion(user.id)
    autoStartAttemptedRef.current = user.id
    driverRef.current?.destroy()
    window.setTimeout(startTour, NEXT_PAINT_DELAY_MS)
  }, [startTour, user])

  const registerCoachActions = useCallback((actions: ProductTourActions | null) => {
    coachActionsRef.current = actions
  }, [])

  useEffect(() => {
    if (status !== 'authenticated' || !user || hasCompletedProductTour(user.id)) return
    if (autoStartAttemptedRef.current === user.id) return
    if (location.pathname === '/login' || location.pathname === '/register') return

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
    <ProductTourContext.Provider value={{ startTour, replayTour, registerCoachActions }}>
      {children}
    </ProductTourContext.Provider>
  )
}

export function useProductTour() {
  const value = useContext(ProductTourContext)
  if (!value) throw new Error('useProductTour must be used within ProductTourProvider')
  return value
}
