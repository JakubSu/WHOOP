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
    <main className="grid min-h-screen bg-background lg:grid-cols-[1.1fr_.9fr]">
      <section className="flex items-center px-6 py-12 sm:px-10 lg:px-20" aria-labelledby="page-title">
        <div className="mx-auto w-full max-w-xl">
          <div className="mb-8 grid size-12 place-items-center rounded-lg bg-foreground text-background">{icon}</div>
          <p className="text-xs font-bold uppercase tracking-[.16em] text-primary">{eyebrow}</p>
          <h1 id="page-title" className="mt-3 max-w-md text-4xl font-bold tracking-tight text-foreground sm:text-5xl">{title}</h1>
          <p className="mt-5 max-w-lg leading-7 text-muted-foreground">{description}</p>
        </div>
      </section>
      <section className="flex items-center border-t border-border bg-card/60 px-6 py-10 sm:px-10 lg:border-l lg:border-t-0 lg:px-16 lg:py-20">
        <div className="mx-auto w-full max-w-md">{children}</div>
      </section>
    </main>
  )
}
