import {
  createContext,
  type Dispatch,
  type ReactNode,
  type SetStateAction,
  useContext,
  useEffect,
  useMemo,
  useState,
} from 'react'
import {
  areCoachContextsEqual,
  coachContextKey,
  type CoachViewContext,
} from '../services/coachContext'

type CoachOverlayContextValue = {
  currentContext: CoachViewContext | null
  setCurrentContext: Dispatch<SetStateAction<CoachViewContext | null>>
}

const CoachOverlayContext = createContext<CoachOverlayContextValue | null>(null)

export function CoachOverlayProvider({ children }: { children: ReactNode }) {
  const [currentContext, setCurrentContext] =
    useState<CoachViewContext | null>(null)
  const value = useMemo(
    () => ({
      currentContext,
      setCurrentContext,
    }),
    [currentContext],
  )

  return (
    <CoachOverlayContext.Provider value={value}>
      {children}
    </CoachOverlayContext.Provider>
  )
}

export function useCoachOverlayContext() {
  const value = useContext(CoachOverlayContext)
  if (!value) {
    throw new Error('useCoachOverlayContext must be used within CoachOverlayProvider')
  }

  return value
}

export function useCoachPageContext(context: CoachViewContext | null) {
  const { setCurrentContext } = useCoachOverlayContext()
  const key = context ? coachContextKey(context) : 'none'
  const stableContext = useMemo(() => context, [key])

  useEffect(() => {
    setCurrentContext((latest) =>
      areCoachContextsEqual(latest, stableContext) ? latest : stableContext,
    )
    return () => {
      setCurrentContext((latest) =>
        areCoachContextsEqual(latest, stableContext) ? null : latest,
      )
    }
  }, [key, setCurrentContext, stableContext])
}
