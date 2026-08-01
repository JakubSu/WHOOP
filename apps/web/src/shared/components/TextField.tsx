import { useId } from 'react'
import { Input, Label } from './ui'

type TextFieldProps = {
  label: string
  name: string
  value: string
  onChange: (value: string) => void
  type?: string
  autoComplete?: string
}

export function TextField({
  label,
  name,
  value,
  onChange,
  type = 'text',
  autoComplete,
}: TextFieldProps) {
  const id = useId()

  return (
    <div className="grid gap-2">
      <Label htmlFor={id}>{label}</Label>
      <Input
        id={id}
        name={name}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </div>
  )
}
