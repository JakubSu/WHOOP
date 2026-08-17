import { type FormEvent, useId, useState } from 'react'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AuthRedirectLink } from '../components/AuthRedirectLink'
import { useLogin } from '../hooks/useLogin'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { Button, Input, Label } from '../../../shared/components/ui'
import { isValidEmail } from '../../../shared/utils/validation'

export function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const emailId = useId()
  const passwordId = useId()

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
      navigate('/', { replace: true })
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
      <form className="grid gap-5" onSubmit={handleSubmit}>
        <div className="grid gap-2">
          <Label htmlFor={emailId}>Email</Label>
          <Input id={emailId} name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        </div>
        <div className="grid gap-2">
          <Label htmlFor={passwordId}>Password</Label>
          <div className="relative">
            <Input className="pr-12" id={passwordId} name="password" type={isPasswordVisible ? 'text' : 'password'} autoComplete="current-password" value={password} onChange={(event) => setPassword(event.target.value)} />
            <Button className="absolute right-0 top-0 text-muted-foreground hover:text-foreground" type="button" variant="ghost" size="icon" aria-label={isPasswordVisible ? 'Hide password' : 'Show password'} onClick={() => setIsPasswordVisible((visible) => !visible)}>
              {isPasswordVisible ? <EyeOff aria-hidden="true" size={18} /> : <Eye aria-hidden="true" size={18} />}
            </Button>
          </div>
        </div>
        <InlineError message={formError} />
        <PrimaryButton className="mt-1 w-full" type="submit" isLoading={login.isPending}>
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
