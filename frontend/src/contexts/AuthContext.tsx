import { createContext, useContext, useEffect, useState } from 'react'
import type { ReactNode } from 'react'
import type { AuthUser } from '../lib/auth'
import { clearToken, fetchCurrentUser } from '../lib/auth'

interface AuthContextValue {
  user: AuthUser | null
  loading: boolean
  logout: () => void
  refreshUser: () => Promise<void>
}

const AuthContext = createContext<AuthContextValue | null>(null)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [user, setUser] = useState<AuthUser | null>(null)
  const [loading, setLoading] = useState(true)

  const refreshUser = async () => {
    const u = await fetchCurrentUser()
    setUser(u)
  }

  useEffect(() => {
    refreshUser().finally(() => setLoading(false))
  }, [])

  const logout = () => {
    clearToken()
    setUser(null)
    window.location.href = '/login'
  }

  return (
    <AuthContext.Provider value={{ user, loading, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext)
  if (!ctx) throw new Error('useAuth must be used inside AuthProvider')
  return ctx
}
