export type UserRole = 'user' | 'admin'

export interface UserInfo {
  id: string
  username: string
  role: UserRole
  email?: string
  phone?: string
  status: 'active' | 'disabled'
}

