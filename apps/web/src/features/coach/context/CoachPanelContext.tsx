import { createContext, type ReactNode, useContext, useState } from 'react'

export type CoachPanelMode = 'collapsed' | 'open' | 'expanded'

type CoachPanelContextValue = {
  mode: CoachPanelMode
  open: () => void
  collapse: () => void
  expand: () => void
}

const CoachPanelContext = createContext<CoachPanelContextValue | null>(null)

export function CoachPanelProvider({ children }: { children: ReactNode }) {
  const [mode, setMode] = useState<CoachPanelMode>('open')

  return (
    <CoachPanelContext.Provider value={{
      mode,
      open: () => setMode('open'),
      collapse: () => setMode('collapsed'),
      expand: () => setMode('expanded'),
    }}>
      {children}
    </CoachPanelContext.Provider>
  )
}

export function useCoachPanel() {
  const value = useContext(CoachPanelContext)
  if (!value) throw new Error('useCoachPanel must be used within CoachPanelProvider')
  return value
}
