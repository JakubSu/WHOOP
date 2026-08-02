type InlineErrorProps = {
  message: string | null
}

export function InlineError({ message }: InlineErrorProps) {
  if (!message) {
    return null
  }

  return (
    <Alert>
      {message}
    </Alert>
  )
}
import { Alert } from './ui'
