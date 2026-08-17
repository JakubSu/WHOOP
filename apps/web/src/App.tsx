import { AppProviders } from './app/providers/AppProviders'
import { AppRouter } from './app/router/AppRouter'
import { CoachOverlayProvider } from './features/coach/context/CoachOverlayContext'

function App() {
  return (
    <AppProviders>
      <CoachOverlayProvider>
        <AppRouter />
      </CoachOverlayProvider>
    </AppProviders>
  )
}

export default App
