import { type FormEvent, useId, useState } from 'react'
import { Eye, EyeOff, LogIn } from 'lucide-react'
import { useNavigate } from 'react-router-dom'
import { useMutation } from '@tanstack/react-query'
import { AuthRedirectLink } from '../components/AuthRedirectLink'
import { useLogin } from '../hooks/useLogin'
import { createDemoSession } from '../api/authApi'
import { useAuthStore } from '../store/authStore'
import { saveDemoSession } from '../services/demoSessionStorage'
import { getErrorMessage } from '../../../shared/api/errors'
import { AuthShell } from '../../../shared/components/AuthShell'
import { InlineError } from '../../../shared/components/InlineError'
import { PrimaryButton } from '../../../shared/components/PrimaryButton'
import { Button, Input, Label } from '../../../shared/components/ui'
import { isValidEmail } from '../../../shared/utils/validation'

export function LoginPage() {
  const navigate = useNavigate()
  const login = useLogin()
  const setSession = useAuthStore((state) => state.setSession)
  const demo = useMutation({
    mutationFn: createDemoSession,
    onSuccess: (session) => {
      saveDemoSession(session)
      setSession(session.access, session.user)
      navigate('/', { replace: true })
    },
  })
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
      <div className="my-6 flex items-center gap-3" aria-hidden="true">
        <div className="h-px flex-1 bg-border" />
        <span className="text-xs font-bold uppercase tracking-[.16em] text-muted-foreground">Or</span>
        <div className="h-px flex-1 bg-border" />
      </div>
      <div className="relative overflow-hidden rounded-xl border border-primary/30 bg-accent/45 p-4 text-left shadow-sm">
        <div className="pointer-events-none absolute -right-8 -top-10 size-28 rounded-full bg-primary/10" aria-hidden="true" />
        <div className="relative flex items-start gap-3">
          <img
            className="size-11 shrink-0 rounded-full ring-4 ring-background"
            src="/favicon.svg"
            alt=""
            aria-hidden="true"
          />
          <div>
            <p className="text-sm font-bold text-foreground">Meet your AI Coach</p>
            <p className="mt-1 text-sm leading-5 text-muted-foreground">
              Explore the workspace with sample training data—no account needed.
            </p>
          </div>
        </div>
        <Button className="relative mt-4 w-full shadow-sm" type="button" disabled={demo.isPending} onClick={() => demo.mutate()}>
          {demo.isPending ? 'Starting demo…' : 'Try the demo'}
        </Button>
        <InlineError message={demo.error ? getErrorMessage(demo.error) : null} />
      </div>
    </AuthShell>
  )
}
