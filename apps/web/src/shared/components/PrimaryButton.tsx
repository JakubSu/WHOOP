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
      className={`inline-flex h-11 items-center justify-center gap-2 rounded-md bg-primary px-4 font-semibold text-primary-foreground transition-colors hover:bg-primary/90 disabled:pointer-events-none disabled:opacity-50 ${className ?? ''}`}
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
