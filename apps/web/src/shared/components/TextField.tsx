import { useId } from 'react'

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
    <label className="field" htmlFor={id}>
      <span>{label}</span>
      <input
        id={id}
        name={name}
        type={type}
        autoComplete={autoComplete}
        value={value}
        onChange={(event) => onChange(event.target.value)}
      />
    </label>
  )
}
