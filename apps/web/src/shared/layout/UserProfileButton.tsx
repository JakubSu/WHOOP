import { useMutation, useQueryClient } from '@tanstack/react-query'
import { LogOut, Unlink, Watch } from 'lucide-react'
import { useEffect, useRef, useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { logoutUser } from '../../features/auth/api/authApi'
import { useAuthStore } from '../../features/auth/store/authStore'
import { disconnectWhoop } from '../../features/whoop/api/whoopApi'

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
  const [isOpen, setIsOpen] = useState(false)
  const containerRef = useRef<HTMLDivElement | null>(null)
  const logout = useMutation({
    mutationFn: logoutUser,
    onSettled: async () => {
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
      setIsOpen(false)
    },
  })

  useEffect(() => {
    function handlePointerDown(event: MouseEvent) {
      if (!containerRef.current?.contains(event.target as Node)) {
        setIsOpen(false)
      }
    }

    function handleEscape(event: KeyboardEvent) {
      if (event.key === 'Escape') {
        setIsOpen(false)
      }
    }

    document.addEventListener('mousedown', handlePointerDown)
    document.addEventListener('keydown', handleEscape)

    return () => {
      document.removeEventListener('mousedown', handlePointerDown)
      document.removeEventListener('keydown', handleEscape)
    }
  }, [])

  return (
    <div ref={containerRef} className="profile-menu">
      <button
        className="profile-button"
        type="button"
        aria-label="User profile"
        aria-expanded={isOpen}
        aria-haspopup="menu"
        onClick={() => setIsOpen((open) => !open)}
      >
        {initialsFor(user?.display_name, user?.email)}
      </button>
      {isOpen ? (
        <div className="profile-popover" role="menu" aria-label="Profile menu">
          <div className="profile-popover__identity">
            <strong>{user?.display_name || 'User'}</strong>
            <span>{user?.email}</span>
          </div>
          {user?.whoop_user_id ? (
            <button
              className="profile-popover__action"
              type="button"
              role="menuitem"
              disabled={disconnect.isPending || logout.isPending}
              onClick={() => disconnect.mutate()}
            >
              <Unlink aria-hidden="true" size={16} />
              {disconnect.isPending ? 'Disconnecting WHOOP' : 'Disconnect WHOOP'}
            </button>
          ) : (
            <button
              className="profile-popover__action"
              type="button"
              role="menuitem"
              disabled={logout.isPending}
              onClick={() => {
                setIsOpen(false)
                navigate('/connect-whoop')
              }}
            >
              <Watch aria-hidden="true" size={16} />
              Connect WHOOP
            </button>
          )}
          <button
            className="profile-popover__action"
            type="button"
            role="menuitem"
            disabled={logout.isPending || disconnect.isPending}
            onClick={() => logout.mutate()}
          >
            <LogOut aria-hidden="true" size={16} />
            {logout.isPending ? 'Signing out' : 'Log out'}
          </button>
        </div>
      ) : null}
    </div>
  )
}
