import { useEffect, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { useWhoopSummary } from '../../features/whoop/hooks/useWhoopSummary'
import { useAuthStore } from '../../features/auth/store/authStore'
import { getErrorMessage } from '../api/errors'
import { Button, Dialog, DialogContent, DialogTitle } from '../components/ui'

const DISMISS_KEY = 'whoop-connection-prompt-dismissed'

export function WhoopConnectionPrompt() {
  const navigate = useNavigate()
  const user = useAuthStore((state) => state.user)
  const summary = useWhoopSummary()
  const [isDismissed, setIsDismissed] = useState(() => {
    if (typeof window === 'undefined') {
      return false
    }

    return window.sessionStorage.getItem(DISMISS_KEY) === 'true'
  })

  const needsPrompt =
    user?.account_type !== 'demo' &&
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

  function dismiss() {
    window.sessionStorage.setItem(DISMISS_KEY, 'true')
    setIsDismissed(true)
  }

  return (
    <Dialog open onOpenChange={(open) => { if (!open) dismiss() }}>
      <DialogContent className="max-h-[calc(100dvh-2rem)] overflow-y-auto p-5 sm:p-6" aria-describedby="whoop-modal-copy">
        <p className="text-xs font-bold uppercase tracking-[.16em] text-primary">WHOOP connection</p>
        <DialogTitle className="mt-2 text-xl font-bold tracking-tight">Connect WHOOP to load your metrics</DialogTitle>
        <p id="whoop-modal-copy" className="mt-3 text-sm leading-6 text-muted-foreground">{detailFor(summary)}</p>
        <div className="mt-5 flex flex-col-reverse gap-2 sm:flex-row sm:justify-end">
          <Button className="w-full sm:w-auto" type="button" variant="ghost" onClick={dismiss}>Continue without WHOOP</Button>
          <Button className="w-full sm:w-auto" type="button" onClick={() => navigate('/connect-whoop')}>Connect WHOOP</Button>
        </div>
      </DialogContent>
    </Dialog>
  )
}

function detailFor(summary: ReturnType<typeof useWhoopSummary>) {
  if (summary.isError) {
    return `We couldn't load your WHOOP summary right now. ${getErrorMessage(summary.error)}`
  }

  return 'Your WHOOP account is not connected yet. Connect it now to load recovery, sleep, and strain in the app.'
}
