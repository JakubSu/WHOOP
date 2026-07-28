import { AppProviders } from './app/providers/AppProviders'
import { AppRouter } from './app/router/AppRouter'
import { CoachOverlay } from './features/coach/components/CoachOverlay'
import { CoachOverlayProvider } from './features/coach/context/CoachOverlayContext'

function App() {
  return (
    <AppProviders>
      <CoachOverlayProvider>
        <AppRouter />
        <CoachOverlay />
      </CoachOverlayProvider>
    </AppProviders>
  )
}

export default App
