import { type FormEvent, useId, useState } from 'react'
import { Eye, EyeOff, UserPlus } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { AuthRedirectLink } from '../components/AuthRedirectLink'
import { useRegister } from '../hooks/useRegister'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { Button, Input, Label } from '../../../shared/components/ui'
import { isValidEmail } from '../../../shared/utils/validation'

export function RegisterPage() {
  const navigate = useNavigate()
  const register = useRegister()
  const [displayName, setDisplayName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [isPasswordVisible, setIsPasswordVisible] = useState(false)
  const [formError, setFormError] = useState<string | null>(null)
  const displayNameId = useId()
  const emailId = useId()
  const passwordId = useId()

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
      <form className="grid gap-5" onSubmit={handleSubmit}>
        <div className="grid gap-2">
          <Label htmlFor={displayNameId}>Full name</Label>
          <Input id={displayNameId} name="displayName" autoComplete="name" value={displayName} onChange={(event) => setDisplayName(event.target.value)} />
        </div>
        <div className="grid gap-2">
          <Label htmlFor={emailId}>Email</Label>
          <Input id={emailId} name="email" type="email" autoComplete="email" value={email} onChange={(event) => setEmail(event.target.value)} />
        </div>
        <div className="grid gap-2">
          <Label htmlFor={passwordId}>Password</Label>
          <div className="relative">
            <Input className="pr-12" id={passwordId} name="password" type={isPasswordVisible ? 'text' : 'password'} autoComplete="new-password" value={password} onChange={(event) => setPassword(event.target.value)} />
            <Button className="absolute right-0 top-0 text-muted-foreground hover:text-foreground" type="button" variant="ghost" size="icon" aria-label={isPasswordVisible ? 'Hide password' : 'Show password'} onClick={() => setIsPasswordVisible((visible) => !visible)}>
              {isPasswordVisible ? <EyeOff aria-hidden="true" size={18} /> : <Eye aria-hidden="true" size={18} />}
            </Button>
          </div>
          <p className="text-xs text-muted-foreground">Use at least 8 characters.</p>
        </div>
        <InlineError message={formError} />
        <PrimaryButton className="mt-1 w-full" type="submit" isLoading={register.isPending}>
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
