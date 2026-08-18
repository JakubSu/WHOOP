import { AppProviders } from './app/providers/AppProviders'
import { AppRouter } from './app/router/AppRouter'
import { CoachOverlayProvider } from './features/coach/context/CoachOverlayContext'
import { ProductTourProvider } from './features/product-tour/ProductTourProvider'

function App() {
  return (
    <AppProviders>
      <ProductTourProvider>
        <CoachOverlayProvider>
          <AppRouter />
        </CoachOverlayProvider>
      </ProductTourProvider>
    </AppProviders>
  )
}

export default App
