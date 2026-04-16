import { create } from 'zustand'
import { persist } from 'zustand/middleware'
import { login as apiLogin, logout as apiLogout } from '@/api/endpoints'

interface AuthState {
  isAuthenticated: boolean
  sessionId: string | null
  login: (mpin: string) => Promise<boolean>
  logout: () => Promise<void>
  setAuthenticated: (sessionId: string) => void
}

export const useAuthStore = create<AuthState>()(
  persist(
    (set) => ({
      isAuthenticated: false,
      sessionId: null,

      login: async (mpin: string) => {
        try {
          const response = await apiLogin(mpin)
          if (response.success) {
            set({ isAuthenticated: true, sessionId: response.session_id })
            return true
          }
          return false
        } catch {
          return false
        }
      },

      logout: async () => {
        try {
          await apiLogout()
        } finally {
          set({ isAuthenticated: false, sessionId: null })
        }
      },

      setAuthenticated: (sessionId: string) => {
        set({ isAuthenticated: true, sessionId })
      },
    }),
    {
      name: 'auth-storage',
      partialize: (state) => ({ sessionId: state.sessionId, isAuthenticated: state.isAuthenticated }),
    }
  )
)
