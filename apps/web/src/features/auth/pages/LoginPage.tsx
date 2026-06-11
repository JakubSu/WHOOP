import { type FormEvent, useState } from 'react'
import { LogIn } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AuthRedirectLink } from '../components/AuthRedirectLink'
import { useLogin } from '../hooks/useLogin'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { PasswordField } from '../../../shared/components/PasswordField'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { TextField } from '../../../shared/components/TextField'
import { isValidEmail } from '../../../shared/utils/validation'

export function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    if (!isValidEmail(email)) {
      setFormError('Enter a valid email address.')
      return
    }

    if (!password) {
      setFormError('Enter your password.')
      return
    }

    try {
      await login.mutateAsync({ email, password })
      navigate('/plan', { replace: true })
    } catch (error) {
      setFormError(getErrorMessage(error))
    }
  }

  return (
    <AuthShell
      eyebrow="Welcome back"
      title="Sign in"
      description="Access your coach workspace and continue your training flow."
      icon={<LogIn aria-hidden="true" />}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <TextField
          label="Email"
          name="email"
          type="email"
          autoComplete="email"
          value={email}
          onChange={setEmail}
        />
        <PasswordField
          label="Password"
          name="password"
          autoComplete="current-password"
          value={password}
          onChange={setPassword}
        />
        <InlineError message={formError} />
        <PrimaryButton type="submit" isLoading={login.isPending}>
          Sign in
        </PrimaryButton>
      </form>
      <AuthRedirectLink
        prompt="Need an account?"
        label="Create one"
        to="/register"
      />
    </AuthShell>
  )
}
