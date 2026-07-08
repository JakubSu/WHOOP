import { Watch } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { ConnectWhoopButton } from '../components/ConnectWhoopButton'
import { useConnectWhoop } from '../hooks/useConnectWhoop'

export function ConnectWhoopPage() {
  const connectWhoop = useConnectWhoop()
  const [error, setError] = useState<string | null>(null)
  const [connectUrl, setConnectUrl] = useState<string | null>(null)

  async function handleConnect() {
    setError(null)
    setConnectUrl(null)

    try {
      const successUrl = new URL('/connect-whoop/success', window.location.origin)
      const { connect_url } = await connectWhoop.mutateAsync({
        successUrl: successUrl.toString(),
      })

      const url = new URL(connect_url)
      if (url.protocol !== 'https:') {
        throw new Error('The WHOOP connect URL is not valid.')
      }

      setConnectUrl(connect_url)
      window.location.assign(url.toString())
    } catch (requestError) {
      setError(getConnectErrorMessage(requestError))
    }
  }

  return (
    <AuthShell
      eyebrow="WHOOP connection"
      title="Connect WHOOP"
      description="Link your WHOOP data so your coach can use recovery, sleep, and strain context."
      icon={<Watch aria-hidden="true" />}
    >
      <div className="connect-panel">
        <div className="flow-note">
          <p>
            We ask the API for a fresh WHOOP authorization link, then send this
            browser directly to WHOOP.
          </p>
          <p>If WHOOP is unavailable, you can continue and connect it later.</p>
        </div>
        <ConnectWhoopButton
          isLoading={connectWhoop.isPending}
          onClick={handleConnect}
        />
        {connectUrl ? (
          <a className="primary-button secondary-action" href={connectUrl}>
            Continue to WHOOP
          </a>
        ) : null}
        <Link className="primary-button secondary-action" to="/training">
          Continue without WHOOP
        </Link>
        <InlineError message={error} />
      </div>
    </AuthShell>
  )
}

function getConnectErrorMessage(error: unknown) {
  const detail = getErrorMessage(error)

  if (detail === 'The WHOOP connect URL is not valid.') {
    return detail
  }

  return `WHOOP connection is temporarily unavailable. ${detail}`
}
