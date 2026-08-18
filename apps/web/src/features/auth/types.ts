export type UserProfile = {
  id: string
  email: string
  display_name: string
  whoop_user_id?: string
  account_type: 'normal' | 'demo'
  expires_at?: string | null
  created_at?: string
  updated_at?: string
}

export type AuthSession = {
  user: UserProfile
  access: string
  refresh?: string
}

export type TokenPair = {
  access: string
  refresh?: string
}

export type RegisterPayload = {
  email: string
  password: string
  display_name: string
}

export type LoginPayload = {
  email: string
  password: string
}
