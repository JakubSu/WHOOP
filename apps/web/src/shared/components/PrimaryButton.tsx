import { LoaderCircle } from 'lucide-react'
import { type ButtonHTMLAttributes, type ReactNode } from 'react'

type PrimaryButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  children: ReactNode
  isLoading?: boolean
}

export function PrimaryButton({
  children,
  isLoading = false,
  disabled,
  className,
  ...props
}: PrimaryButtonProps) {
  return (
    <button
      className={className ? `primary-button ${className}` : 'primary-button'}
      disabled={disabled || isLoading}
      {...props}
    >
      {isLoading ? (
        <>
          <LoaderCircle className="spin" aria-hidden="true" size={18} />
          Working
        </>
      ) : (
        children
      )}
    </button>
  )
}
