import { Eye, EyeOff } from 'lucide-react'
import { useId, useState } from 'react'
import { Button, Input, Label } from './ui'

type PasswordFieldProps = {
  label: string
  name: string
  value: string
  autoComplete: string
  onChange: (value: string) => void
}

export function PasswordField({
  label,
  name,
  value,
  autoComplete,
  onChange,
}: PasswordFieldProps) {
  const id = useId()
  const [isVisible, setIsVisible] = useState(false)

  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <div className="relative">
        <Input className="pr-12"
          id={id}
          name={name}
          type={isVisible ? 'text' : 'password'}
          autoComplete={autoComplete}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
        <Button
          type="button"
          aria-label={isVisible ? 'Hide password' : 'Show password'}
          className="absolute right-0 top-0 text-muted-foreground hover:text-foreground"
          variant="secondary" size="icon"
          onClick={() => setIsVisible((current) => !current)}
        >
          {isVisible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
        </Button>
      </div>
    </div>
  )
}
