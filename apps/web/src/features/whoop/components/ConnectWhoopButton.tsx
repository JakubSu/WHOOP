import { Watch } from 'lucide-react'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'

type ConnectWhoopButtonProps = {
  isLoading: boolean
  onClick: () => void
}

export function ConnectWhoopButton({
  isLoading,
  onClick,
}: ConnectWhoopButtonProps) {
  return (
    <PrimaryButton type="button" isLoading={isLoading} onClick={onClick}>
      <Watch aria-hidden="true" size={18} />
      Connect to WHOOP
    </PrimaryButton>
  )
}
