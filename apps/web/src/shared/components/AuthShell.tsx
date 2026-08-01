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
    <main className="grid min-h-screen bg-background lg:grid-cols-[1fr_.8fr]">
      <section className="flex flex-col justify-center p-8 lg:p-20" aria-labelledby="page-title">
        <div className="mb-6 grid size-12 place-items-center rounded-lg bg-foreground text-background">{icon}</div>
        <p className="mb-3 text-xs font-bold uppercase tracking-[.16em] text-primary">{eyebrow}</p>
        <h1 id="page-title" className="max-w-md text-5xl font-bold tracking-tight">{title}</h1>
        <p className="mt-5 max-w-xl text-muted-foreground">{description}</p>
      </section>
      <section className="flex flex-col justify-center border-t border-border bg-card/60 p-8 lg:border-l lg:border-t-0 lg:p-20">{children}</section>
    </main>
  )
}
