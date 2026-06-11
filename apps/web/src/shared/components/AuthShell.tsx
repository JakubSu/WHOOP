import { type ReactNode } from 'react'

type AuthShellProps = {
  eyebrow: string
  title: string
  description: string
  icon: ReactNode
  children: ReactNode
}

export function AuthShell({
  eyebrow,
  title,
  description,
  icon,
  children,
}: AuthShellProps) {
  return (
    <main className="auth-shell">
      <section className="auth-intro" aria-labelledby="page-title">
        <div className="brand-mark">{icon}</div>
        <p className="eyebrow">{eyebrow}</p>
        <h1 id="page-title">{title}</h1>
        <p>{description}</p>
      </section>
      <section className="auth-panel">{children}</section>
    </main>
  )
}
