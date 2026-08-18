import { Watch } from 'lucide-react'
import { Button, Spinner } from '../../../shared/components/ui'

type ConnectWhoopButtonProps = {
  isLoading: boolean
  isRedirecting?: boolean
  onClick: () => void
}

export function ConnectWhoopButton({
  isLoading,
  isRedirecting = false,
  onClick,
}: ConnectWhoopButtonProps) {
  return (
    <Button className="w-full sm:w-auto" type="button" disabled={isLoading} onClick={onClick}>
      {isLoading ? <Spinner className="size-[18px]" /> : <Watch aria-hidden="true" size={18} />}
      {isRedirecting ? 'Redirecting to WHOOP…' : isLoading ? 'Opening WHOOP…' : 'Connect to WHOOP'}
    </Button>
  )
}
