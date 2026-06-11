import { Eye, EyeOff } from 'lucide-react'
import { useId, useState } from 'react'

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
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <span className="password-control">
        <input
          id={id}
          name={name}
          type={isVisible ? 'text' : 'password'}
          autoComplete={autoComplete}
          value={value}
          onChange={(event) => onChange(event.target.value)}
        />
        <button
          type="button"
          aria-label={isVisible ? 'Hide password' : 'Show password'}
          className="icon-button"
          onClick={() => setIsVisible((current) => !current)}
        >
          {isVisible ? <EyeOff aria-hidden="true" /> : <Eye aria-hidden="true" />}
        </button>
      </span>
    </label>
  )
}
