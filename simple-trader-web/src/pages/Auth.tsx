import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import { nubraLogin, checkNubraStatus } from '@/api/endpoints'

export default function Auth() {
  const [totp, setTotp] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(true)
  const navigate = useNavigate()

  // Get auth store method
  const setAuthenticated = useAuthStore((state) => state.setAuthenticated)

  // Check if already authenticated with Nubra
  useEffect(() => {
    checkNubraAuth()
  }, [])

  const checkNubraAuth = async () => {
    setCheckingStatus(true)
    try {
      const status = await checkNubraStatus()
      setIsAuthenticated(status.authenticated)
      if (status.authenticated) {
        setSuccess('Nubra is already authenticated. Session is active.')
        // Also update auth store so user can access protected routes
        const sessionId = localStorage.getItem('sessionId')
        if (sessionId) {
          setAuthenticated(sessionId)
        }
      }
    } catch (err) {
      // Not authenticated
      setIsAuthenticated(false)
    } finally {
      setCheckingStatus(false)
    }
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (!totp || totp.length !== 6) {
      setError('Please enter the 6-digit TOTP code from your authenticator app')
      setLoading(false)
      return
    }

    try {
      const response = await nubraLogin({
        totp
      })

      if (response.success) {
        setSuccess(response.message || 'Successfully authenticated!')
        setIsAuthenticated(true)

        // Update auth store to mark as authenticated
        if (response.session_id) {
          setAuthenticated(response.session_id)
        }

        // Wait a moment to show success message
        setTimeout(() => {
          navigate('/')
        }, 1500)
      } else {
        setError(response.message || 'Authentication failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleSkip = () => {
    navigate('/')
  }

  if (checkingStatus) {
    return (
      <div className="flex h-screen w-full items-center justify-center bg-background">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary mx-auto"></div>
          <p className="mt-4 text-muted-foreground">Checking authentication status...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
            <Lock className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">SimpleTrader</h1>
          <p className="mt-2 text-muted-foreground">
            {isAuthenticated
              ? 'Nubra broker is authenticated'
              : 'Enter TOTP code from your authenticator app'}
          </p>
        </div>

        {isAuthenticated ? (
          <div className="space-y-4">
            <div className="p-4 bg-success/10 border border-success/20 rounded-lg">
              <div className="flex items-center gap-2 text-success">
                <CheckCircle className="h-5 w-5" />
                <p className="font-medium">Already Authenticated</p>
              </div>
              <p className="mt-2 text-sm text-muted-foreground">
                Your Nubra session is active. You can access all trading features.
              </p>
            </div>

            <Button onClick={handleSkip} className="w-full">
              Continue to Dashboard
            </Button>

            <Button
              onClick={() => setIsAuthenticated(false)}
              variant="outline"
              className="w-full"
            >
              Re-authenticate
            </Button>
          </div>
        ) : (
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="totp" className="text-sm font-medium block">
                TOTP Code
              </label>
              <Input
                id="totp"
                type="text"
                placeholder="000000"
                value={totp}
                onChange={(e) => setTotp(e.target.value.replace(/\D/g, ''))}
                maxLength={6}
                className="mt-1 text-center text-2xl font-mono tracking-widest"
                autoComplete="one-time-code"
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Enter the 6-digit code from your authenticator app (Google Authenticator, Authy, etc.)
              </p>
              <div className="p-3 bg-primary/5 border border-primary/10 rounded-lg">
                <p className="text-xs text-muted-foreground">
                  <strong className="text-foreground">First time?</strong> Set up TOTP authentication with Nubra using your authenticator app to scan the QR code
                </p>
              </div>
            </div>

            {error && (
              <div className="flex items-center gap-2 p-3 bg-error/10 border border-error/20 rounded-lg">
                <AlertCircle className="h-4 w-4 text-error flex-shrink-0" />
                <p className="text-sm text-error">{error}</p>
              </div>
            )}

            {success && (
              <div className="flex items-center gap-2 p-3 bg-success/10 border border-success/20 rounded-lg">
                <CheckCircle className="h-4 w-4 text-success flex-shrink-0" />
                <p className="text-sm text-success">{success}</p>
              </div>
            )}

            <Button type="submit" className="w-full" loading={loading}>
              {loading ? 'Authenticating...' : 'Sign In with Nubra'}
            </Button>

            <Button
              type="button"
              onClick={handleSkip}
              variant="ghost"
              className="w-full"
            >
              Skip for Now
            </Button>
          </form>
        )}

        <div className="space-y-2 text-center text-xs text-muted-foreground">
          <p>
            Your session will persist for several days after successful authentication
          </p>
          <p>
            Credentials are processed securely and never stored on disk
          </p>
        </div>
      </div>
    </div>
  )
}
