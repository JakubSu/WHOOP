import * as AvatarPrimitive from '@radix-ui/react-avatar'
import * as DialogPrimitive from '@radix-ui/react-dialog'
import * as DropdownMenuPrimitive from '@radix-ui/react-dropdown-menu'
import * as ScrollAreaPrimitive from '@radix-ui/react-scroll-area'
import * as SlotPrimitive from '@radix-ui/react-slot'
import * as TooltipPrimitive from '@radix-ui/react-tooltip'
import { LoaderCircle } from 'lucide-react'
import { type ButtonHTMLAttributes, type ComponentProps, type HTMLAttributes, forwardRef } from 'react'
import { cn } from '@/shared/utils/cn'

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { asChild?: boolean; variant?: 'default'|'secondary'|'outline'|'destructive'|'ghost'; size?: 'default'|'sm'|'icon' }>(({ className, variant='default', size='default', asChild = false, ...props }, ref) => {
  const Component = asChild ? SlotPrimitive.Slot : 'button'
  return <Component ref={ref} className={cn('inline-flex cursor-pointer items-center justify-center gap-2 rounded-md font-semibold transition-colors focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring disabled:cursor-not-allowed disabled:opacity-50', variant === 'default' && 'bg-primary text-primary-foreground hover:bg-primary/90', variant === 'secondary' && 'bg-secondary text-secondary-foreground hover:bg-secondary/80', variant === 'outline' && 'border border-border bg-background hover:bg-accent hover:text-accent-foreground', variant === 'destructive' && 'bg-destructive text-destructive-foreground hover:bg-destructive/90', variant === 'ghost' && 'hover:bg-accent hover:text-accent-foreground', size === 'default' && 'h-11 px-4', size === 'sm' && 'h-9 px-3 text-sm', size === 'icon' && 'size-10', className)} {...props} />
})
Button.displayName = 'Button'
export function Card({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div className={cn('rounded-lg border border-border bg-card text-card-foreground shadow-sm', className)} {...props} /> }
export const Input = forwardRef<HTMLInputElement, React.ComponentProps<'input'>>(({ className, ...props }, ref) => <input ref={ref} className={cn('h-11 w-full rounded-md border border-input bg-background px-3 text-base outline-none placeholder:text-muted-foreground focus-visible:ring-2 focus-visible:ring-ring disabled:opacity-50 sm:text-sm', className)} {...props} />)
Input.displayName='Input'
export function Label({ className, ...props }: React.ComponentProps<'label'>) { return <label className={cn('text-sm font-medium', className)} {...props} /> }
export function Alert({ className, ...props }: HTMLAttributes<HTMLDivElement>) { return <div role="alert" className={cn('rounded-md border border-destructive/30 bg-destructive/10 p-3 text-sm text-destructive', className)} {...props} /> }
export function Badge({ className, ...props }: HTMLAttributes<HTMLSpanElement>) { return <span className={cn('inline-flex w-fit items-center rounded-full border border-border px-2 py-0.5 text-xs font-semibold', className)} {...props} /> }
export const Avatar = AvatarPrimitive.Root; export const AvatarImage = AvatarPrimitive.Image; export function AvatarFallback({className,...props}: React.ComponentProps<typeof AvatarPrimitive.Fallback>) { return <AvatarPrimitive.Fallback className={cn('flex size-10 items-center justify-center rounded-full bg-secondary text-sm font-bold',className)} {...props}/> }
export const DropdownMenu=DropdownMenuPrimitive.Root; export const DropdownMenuTrigger=DropdownMenuPrimitive.Trigger; export function DropdownMenuContent({className,...props}:React.ComponentProps<typeof DropdownMenuPrimitive.Content>){return <DropdownMenuPrimitive.Portal><DropdownMenuPrimitive.Content className={cn('z-50 min-w-52 rounded-md border border-border bg-card p-1 shadow-lg',className)} {...props}/></DropdownMenuPrimitive.Portal>} export function DropdownMenuItem({className,...props}:React.ComponentProps<typeof DropdownMenuPrimitive.Item>){return <DropdownMenuPrimitive.Item className={cn('flex cursor-pointer items-center gap-2 rounded-sm px-2 py-2 text-sm outline-none focus:bg-accent disabled:opacity-50',className)} {...props}/>}
export const Dialog=DialogPrimitive.Root; export const DialogTrigger=DialogPrimitive.Trigger; export function DialogContent({className,...props}:React.ComponentProps<typeof DialogPrimitive.Content>){return <DialogPrimitive.Portal><DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-black/50"/><DialogPrimitive.Content className={cn('fixed left-1/2 top-1/2 z-50 w-[calc(100%-2rem)] max-w-md -translate-x-1/2 -translate-y-1/2 rounded-lg border bg-card p-6 shadow-xl focus:outline-none',className)} {...props}/></DialogPrimitive.Portal>}; export const DialogTitle=DialogPrimitive.Title
export const Sheet = DialogPrimitive.Root
export const SheetTitle = DialogPrimitive.Title
export function SheetContent({ className, ...props }: ComponentProps<typeof DialogPrimitive.Content>) {
  return <DialogPrimitive.Portal>
    <DialogPrimitive.Overlay className="fixed inset-0 z-40 bg-black/50 motion-reduce:transition-none" />
    <DialogPrimitive.Content className={cn('fixed inset-x-0 bottom-0 z-50 flex max-h-[90dvh] flex-col rounded-t-3xl border border-border bg-card text-card-foreground shadow-2xl outline-none', className)} {...props} />
  </DialogPrimitive.Portal>
}
export function ScrollArea({ className, children, viewportRef, onViewportScroll }: HTMLAttributes<HTMLDivElement> & { viewportRef?: React.RefObject<HTMLDivElement | null>; onViewportScroll?: React.UIEventHandler<HTMLDivElement> }) { return <ScrollAreaPrimitive.Root className={cn('overflow-hidden', className)}><ScrollAreaPrimitive.Viewport ref={viewportRef} className="size-full" onScroll={onViewportScroll}>{children}</ScrollAreaPrimitive.Viewport><ScrollAreaPrimitive.Scrollbar className="flex w-2 p-px"><ScrollAreaPrimitive.Thumb className="flex-1 rounded bg-border" /></ScrollAreaPrimitive.Scrollbar></ScrollAreaPrimitive.Root> }
export function Separator({className,...props}:HTMLAttributes<HTMLDivElement>){return <div className={cn('h-px bg-border',className)} {...props}/>} export function Skeleton({className,...props}:HTMLAttributes<HTMLDivElement>){return <div className={cn('animate-pulse rounded bg-muted',className)} {...props}/>} export function Spinner({className}:{className?:string}){return <LoaderCircle className={cn('animate-spin',className)} aria-hidden="true"/>} export const TooltipProvider=TooltipPrimitive.Provider; export const Tooltip=TooltipPrimitive.Root; export const TooltipTrigger=TooltipPrimitive.Trigger; export const TooltipContent=TooltipPrimitive.Content
