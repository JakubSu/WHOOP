type InlineErrorProps = {
  message: string | null
}

export function InlineError({ message }: InlineErrorProps) {
  if (!message) {
    return null
  }

  return (
    <p className="inline-error" role="alert">
      {message}
    </p>
  )
}
