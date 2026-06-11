import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWhoopSummary } from '../../features/whoop/hooks/useWhoopSummary'
import { getErrorMessage } from '../api/errors'
import { PrimaryButton } from '../components/PrimaryButton'

const DISMISS_KEY = 'whoop-connection-prompt-dismissed'

export function WhoopConnectionPrompt() {
  const navigate = useNavigate()
  const summary = useWhoopSummary()
  const [isDismissed, setIsDismissed] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }

    return window.sessionStorage.getItem(DISMISS_KEY) === 'true'
  })

  const needsPrompt =
    !summary.isLoading &&
    (summary.isError || summary.data?.connected === false)

  useEffect(() => {
    if (!summary.isLoading && summary.data?.connected) {
      window.sessionStorage.removeItem(DISMISS_KEY)
      setIsDismissed(false)
    }
  }, [summary.data?.connected, summary.isLoading])

  if (!needsPrompt || isDismissed) {
    return null
  }

  return (
    <div className="whoop-modal-backdrop" role="presentation">
      <section
        className="whoop-modal"
        role="dialog"
        aria-modal="true"
        aria-labelledby="whoop-modal-title"
      >
        <p className="eyebrow">WHOOP connection</p>
        <h2 id="whoop-modal-title">Connect WHOOP to load your metrics</h2>
        <p className="whoop-modal__copy">{detailFor(summary)}</p>
        <div className="whoop-modal__actions">
          <PrimaryButton
            type="button"
            onClick={() => navigate('/connect-whoop')}
          >
            Connect WHOOP
          </PrimaryButton>
          <button
            className="reject-button"
            type="button"
            onClick={() => {
              window.sessionStorage.setItem(DISMISS_KEY, 'true')
              setIsDismissed(true)
            }}
          >
            Continue without WHOOP
          </button>
        </div>
      </section>
    </div>
  )
}

function detailFor(summary: ReturnType<typeof useWhoopSummary>) {
  if (summary.isError) {
    return `We couldn't load your WHOOP summary right now. ${getErrorMessage(summary.error)}`
  }

  return 'Your WHOOP account is not connected yet. Connect it now to load recovery, sleep, and strain in the app.'
}
