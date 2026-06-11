import { type FormEvent, useState } from 'react'
import { UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AuthRedirectLink } from '../components/AuthRedirectLink'
import { useRegister } from '../hooks/useRegister'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { PasswordField } from '../../../shared/components/PasswordField'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { TextField } from '../../../shared/components/TextField'
import { isValidEmail } from '../../../shared/utils/validation'

export function RegisterPage() {
  const navigate = useNavigate()
  const register = useRegister()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [formError, setFormError] = useState<string | null>(null)

  async function handleSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault()
    setFormError(null)

    if (!displayName.trim()) {
      setFormError('Enter your full name.')
      return
    }

    if (!isValidEmail(email)) {
      setFormError('Enter a valid email address.')
      return
    }

    if (password.length < 8) {
      setFormError('Use at least 8 characters for your password.')
      return
    }

    try {
      await register.mutateAsync({
        email,
        password,
        display_name: displayName.trim(),
      })
      navigate('/connect-whoop', { replace: true })
    } catch (error) {
      setFormError(getErrorMessage(error))
    }
  }

  return (
    <AuthShell
      eyebrow="AI Coach"
      title="Create account"
      description="Start with a training profile, then connect WHOOP to personalize your coaching data."
      icon={<UserPlus aria-hidden="true" />}
    >
      <form className="auth-form" onSubmit={handleSubmit}>
        <TextField
          label="Full name"
          name="displayName"
          autoComplete="name"
          value={displayName}
          onChange={setDisplayName}
        />
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
          autoComplete="new-password"
          value={password}
          onChange={setPassword}
        />
        <InlineError message={formError} />
        <PrimaryButton type="submit" isLoading={register.isPending}>
          Register
        </PrimaryButton>
      </form>
      <AuthRedirectLink
        prompt="Already registered?"
        label="Sign in"
        to="/login"
      />
    </AuthShell>
  )
}
