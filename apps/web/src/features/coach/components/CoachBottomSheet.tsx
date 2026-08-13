import { type PointerEventHandler, type ReactNode } from 'react'
import { Sheet, SheetContent } from '../../../shared/components/ui'

type Props = {
  open: boolean
  onOpenChange: (open: boolean) => void
  onDragStart: PointerEventHandler<HTMLElement>
  onDragEnd: PointerEventHandler<HTMLElement>
  children: ReactNode
}

export function CoachBottomSheet({ open, onOpenChange, onDragStart, onDragEnd, children }: Props) {
  return <Sheet open={open} onOpenChange={onOpenChange}>
    <SheetContent className="h-[90dvh] max-h-[90dvh] border-x-0 border-b-0 p-0 duration-200 data-[state=closed]:translate-y-full data-[state=open]:animate-in data-[state=closed]:animate-out data-[state=open]:slide-in-from-bottom data-[state=closed]:slide-out-to-bottom motion-reduce:transition-none" onPointerDownOutside={(event) => event.preventDefault()}>
      <div className="flex justify-center pb-2 pt-3 touch-none" onPointerDown={onDragStart} onPointerUp={onDragEnd} onPointerCancel={onDragEnd}>
        <div className="h-1.5 w-11 rounded-full bg-muted-foreground/35" aria-hidden="true" />
      </div>
      {children}
    </SheetContent>
  </Sheet>
}
