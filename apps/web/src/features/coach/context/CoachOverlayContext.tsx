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
  type CoachPageContext,
} from '../services/coachContext'

type CoachOverlayContextValue = {
  currentContext: CoachPageContext | null
  setCurrentContext: Dispatch<SetStateAction<CoachPageContext | null>>
}

const CoachOverlayContext = createContext<CoachOverlayContextValue | null>(null)

export function CoachOverlayProvider({ children }: { children: ReactNode }) {
  const [currentContext, setCurrentContext] =
    useState<CoachPageContext | null>(null)
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

export function useCoachPageContext(context: CoachPageContext | null) {
  const { setCurrentContext } = useCoachOverlayContext()
  const key = context ? coachContextKey(context) : 'none'

  useEffect(() => {
    setCurrentContext(context)
    return () => {
      setCurrentContext((latest) =>
        areCoachContextsEqual(latest, context) ? null : latest,
      )
    }
  }, [context, key, setCurrentContext])
}
