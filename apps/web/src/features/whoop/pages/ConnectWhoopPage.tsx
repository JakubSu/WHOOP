import { Watch } from 'lucide-react'
import { useState } from 'react'
import { Link } from 'react-router-dom'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { Button, Card, Spinner } from '../../../shared/components/ui'
import { ConnectWhoopButton } from '../components/ConnectWhoopButton'
import {
  useConnectWhoop,
  useRequestWhoopAccess,
  useWhoopAccessRequest,
} from '../hooks/useConnectWhoop'
import { useAuthStore } from '../../auth/store/authStore'

export function ConnectWhoopPage() {
  const user = useAuthStore((state) => state.user)
  const connectWhoop = useConnectWhoop()
  const accessRequest = useWhoopAccessRequest()
  const requestAccess = useRequestWhoopAccess()
  const [error, setError] = useState<string | null>(null)
  const [connectUrl, setConnectUrl] = useState<string | null>(null)
  const [isRedirecting, setIsRedirecting] = useState(false)

  const accessStatus = user?.whoop_connection_allowed
    ? 'approved'
    : accessRequest.data?.status ?? 'none'

  async function handleConnect() {
    if (accessStatus !== 'approved') return
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
      setIsRedirecting(true)
      window.setTimeout(() => window.location.assign(url.toString()), 0)
    } catch (requestError) {
      setIsRedirecting(false)
      setError(getConnectErrorMessage(requestError))
    }
  }

  async function handleRequestAccess() {
    setError(null)
    try {
      await requestAccess.mutateAsync()
    } catch (requestError) {
      setError(getErrorMessage(requestError))
    }
  }

  return (
    <AuthShell
      eyebrow="WHOOP connection"
      title="Connect WHOOP"
      description="Link your WHOOP data so your coach can use recovery, sleep, and strain context."
      icon={<Watch aria-hidden="true" />}
    >
      <div className="grid gap-5">
        <Card className="space-y-3 p-4 text-sm leading-6 text-muted-foreground">
          <p>
            We ask the API for a fresh WHOOP authorization link, then send this
            browser directly to WHOOP.
          </p>
          <p>If WHOOP is unavailable, you can continue and connect it later.</p>
        </Card>
        {accessStatus === 'approved' ? (
          <ConnectWhoopButton
            isLoading={connectWhoop.isPending || isRedirecting}
            isRedirecting={isRedirecting}
            onClick={handleConnect}
          />
        ) : accessStatus === 'pending' ? (
          <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">Your WHOOP access request is pending approval.</p>
        ) : (
          <div className="grid gap-3">
            <p className="rounded-lg border border-border bg-muted p-4 text-sm text-muted-foreground">WHOOP connection is currently available by invitation only.</p>
            <Button
              className="w-full sm:w-auto"
              type="button"
              disabled={requestAccess.isPending || accessRequest.isLoading}
              onClick={handleRequestAccess}
            >
              {requestAccess.isPending || accessRequest.isLoading ? <Spinner className="size-[18px]" /> : null}
              {requestAccess.isPending ? 'Sending request…' : accessStatus === 'rejected' ? 'Request access again' : 'Request WHOOP access'}
            </Button>
          </div>
        )}
        {connectUrl ? (
          <Button asChild className="w-full sm:w-auto" variant="outline">
            <a href={connectUrl}>Continue to WHOOP</a>
          </Button>
        ) : null}
        <Button asChild className="w-full sm:w-auto" variant="ghost"><Link to="/">Continue without WHOOP</Link></Button>
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
