import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, CheckCircle, AlertCircle } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import { nubraLogin, checkNubraStatus } from '@/api/endpoints'

export default function Auth() {
  const [phone, setPhone] = useState('')
  const [mpin, setMpin] = useState('')
  const [otp, setOtp] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [isAuthenticated, setIsAuthenticated] = useState(false)
  const [checkingStatus, setCheckingStatus] = useState(true)
  const login = useAuthStore((state) => state.login)
  const navigate = useNavigate()

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

    if (!phone || phone.length < 10) {
      setError('Please enter a valid 10-digit phone number')
      setLoading(false)
      return
    }

    if (!mpin || mpin.length < 4) {
      setError('Please enter a valid MPIN (4-6 digits)')
      setLoading(false)
      return
    }

    if (!otp || otp.length < 4) {
      setError('Please enter the OTP sent to your phone')
      setLoading(false)
      return
    }

    try {
      const response = await nubraLogin({
        phone,
        mpin,
        otp
      })

      if (response.success) {
        setSuccess(response.message || 'Successfully authenticated!')
        setIsAuthenticated(true)

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
              : 'Sign in with your Nubra broker credentials'}
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
            <div>
              <label htmlFor="phone" className="text-sm font-medium">
                Phone Number
              </label>
              <Input
                id="phone"
                type="tel"
                placeholder="Enter registered phone (10 digits)"
                value={phone}
                onChange={(e) => setPhone(e.target.value)}
                maxLength={10}
                className="mt-1"
                autoComplete="tel"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                Phone number registered with your Nubra broker account
              </p>
            </div>

            <div>
              <label htmlFor="mpin" className="text-sm font-medium">
                MPIN
              </label>
              <Input
                id="mpin"
                type="password"
                placeholder="Enter your broker MPIN"
                value={mpin}
                onChange={(e) => setMpin(e.target.value)}
                maxLength={6}
                className="mt-1"
                autoComplete="off"
              />
            </div>

            <div>
              <label htmlFor="otp" className="text-sm font-medium">
                OTP
              </label>
              <Input
                id="otp"
                type="text"
                placeholder="Enter OTP sent to your phone"
                value={otp}
                onChange={(e) => setOtp(e.target.value)}
                maxLength={6}
                className="mt-1"
                autoComplete="one-time-code"
              />
              <p className="mt-1 text-xs text-muted-foreground">
                An OTP will be sent when you submit the form
              </p>
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
