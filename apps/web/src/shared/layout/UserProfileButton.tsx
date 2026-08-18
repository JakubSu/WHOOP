import { useMutation, useQueryClient } from '@tanstack/react-query'
import { LogOut, Unlink, Watch } from 'lucide-react'
import { useTheme } from 'next-themes'
import { useNavigate } from 'react-router-dom'
import { useProductTour } from '../../features/product-tour/ProductTourProvider'
import { logoutUser } from '../../features/auth/api/authApi'
import { useAuthStore } from '../../features/auth/store/authStore'
import { clearDemoSession } from '../../features/auth/services/demoSessionStorage'
import { disconnectWhoop } from '../../features/whoop/api/whoopApi'
import { Avatar, AvatarFallback, Button, DropdownMenu, DropdownMenuContent, DropdownMenuItem, DropdownMenuTrigger, Separator } from '../components/ui'

function initialsFor(displayName: string | undefined, email: string | undefined) {
  const source = displayName?.trim() || email?.split('@')[0] || 'U'
  const parts = source.split(/\s+/).filter(Boolean)
  return parts
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join('')
}

export function UserProfileButton() {
  const user = useAuthStore((state) => state.user)
  const setUser = useAuthStore((state) => state.setUser)
  const clearSession = useAuthStore((state) => state.clearSession)
  const queryClient = useQueryClient()
  const navigate = useNavigate()
  const { setTheme } = useTheme()
  const { replayTour } = useProductTour()
  const logout = useMutation({
    mutationFn: logoutUser,
    onSettled: async () => {
      clearDemoSession()
      clearSession()
      await queryClient.cancelQueries()
      queryClient.clear()
      navigate('/login', { replace: true })
    },
  })
  const disconnect = useMutation({
    mutationFn: disconnectWhoop,
    onSuccess: async () => {
      if (user) {
        setUser({ ...user, whoop_user_id: '' })
      }
      await queryClient.invalidateQueries({ queryKey: ['whoop-summary'] })
    },
  })

  return (
    <DropdownMenu>
      <DropdownMenuTrigger asChild><Button className="rounded-full border-0 p-0" variant="outline" size="icon" aria-label="User profile"><Avatar className="size-10 overflow-hidden rounded-full"><AvatarFallback>{initialsFor(user?.display_name, user?.email)}</AvatarFallback></Avatar></Button></DropdownMenuTrigger>
      <DropdownMenuContent align="end">
          <div className="px-2 py-2 text-sm"><strong className="block">{user?.display_name || 'User'}</strong><span className="block break-all text-muted-foreground">{user?.email}</span></div><Separator />
          {user?.whoop_user_id ? (
            <DropdownMenuItem
              disabled={disconnect.isPending || logout.isPending || user?.account_type === 'demo'}
              onClick={() => disconnect.mutate()}
            >
              <Unlink aria-hidden="true" size={16} />
              {user?.account_type === 'demo' ? 'WHOOP unavailable in demo' : disconnect.isPending ? 'Disconnecting WHOOP' : 'Disconnect WHOOP'}
            </DropdownMenuItem>
          ) : (
            <DropdownMenuItem
              disabled={logout.isPending || user?.account_type === 'demo'}
              onClick={() => {
                navigate('/connect-whoop')
              }}
            >
              <Watch aria-hidden="true" size={16} />
              {user?.account_type === 'demo' ? 'WHOOP unavailable in demo' : 'Connect WHOOP'}
            </DropdownMenuItem>
          )}
          <DropdownMenuItem
            disabled={logout.isPending || disconnect.isPending}
            onClick={() => logout.mutate()}
          >
            <LogOut aria-hidden="true" size={16} />
            {logout.isPending ? 'Signing out' : 'Log out'}
          </DropdownMenuItem>
          <Separator /><div className="px-2 pb-1 pt-2 text-xs font-semibold text-muted-foreground">Theme</div>
          {(['light','dark','system'] as const).map((theme) => <DropdownMenuItem key={theme} onSelect={() => setTheme(theme)}>{theme[0].toUpperCase() + theme.slice(1)}</DropdownMenuItem>)}
          <Separator />
          <DropdownMenuItem onSelect={replayTour} data-tour="replay-product-tour">Replay product tour</DropdownMenuItem>
      </DropdownMenuContent>
    </DropdownMenu>
  )
}
