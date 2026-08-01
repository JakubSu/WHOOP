import { Link } from 'react-router-dom'

type AuthRedirectLinkProps = {
  prompt: string
  label: string
  to: string
}

export function AuthRedirectLink({ prompt, label, to }: AuthRedirectLinkProps) {
  return (
    <p className="mt-6 text-center text-sm text-muted-foreground">
      {prompt}{' '}
      <Link className="font-semibold text-primary underline-offset-4 hover:underline" to={to}>
        {label}
      </Link>
    </p>
  )
}
