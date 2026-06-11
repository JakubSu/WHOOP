import { Link } from 'react-router-dom'

type AuthRedirectLinkProps = {
  prompt: string
  label: string
  to: string
}

export function AuthRedirectLink({ prompt, label, to }: AuthRedirectLinkProps) {
  return (
    <p className="auth-redirect">
      {prompt} <Link to={to}>{label}</Link>
    </p>
  )
}
