import { useAuthStore } from '@/stores/authStore'

export function useAuth() {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated)
  const sessionId = useAuthStore((state) => state.sessionId)
  const login = useAuthStore((state) => state.login)
  const logout = useAuthStore((state) => state.logout)

  return { isAuthenticated, sessionId, login, logout }
}
