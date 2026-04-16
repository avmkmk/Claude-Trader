import { useState, useEffect } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock, CheckCircle, AlertCircle, Key, QrCode } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'
import {
  nubraLogin,
  checkNubraStatus,
  generateTotpSecret,
  enableTotp,
  type TotpGenerateResponse
} from '@/api/endpoints'

type SetupStep = 'check' | 'generate' | 'enable' | 'login'

export default function Auth() {
  const [step, setStep] = useState<SetupStep>('check')
  const [totp, setTotp] = useState('')
  const [mpin, setMpin] = useState('')
  const [error, setError] = useState('')
  const [success, setSuccess] = useState('')
  const [loading, setLoading] = useState(false)
  const [totpSecret, setTotpSecret] = useState<TotpGenerateResponse | null>(null)
  const navigate = useNavigate()

  const setAuthenticated = useAuthStore((state) => state.setAuthenticated)

  useEffect(() => {
    checkAuthStatus()
  }, [])

  const checkAuthStatus = async () => {
    setStep('check')
    setLoading(true)
    try {
      const status = await checkNubraStatus()
      if (status.authenticated) {
        // Already authenticated, update store and redirect
        let sessionId = localStorage.getItem('sessionId')
        if (!sessionId) {
          sessionId = `nubra-${Date.now()}-${Math.random().toString(36).substring(7)}`
          localStorage.setItem('sessionId', sessionId)
        }
        setAuthenticated(sessionId)
        setSuccess('Already authenticated!')
        setTimeout(() => navigate('/'), 1000)
      } else {
        // Not authenticated, check if we need setup or just login
        if (status.message?.includes('login with TOTP')) {
          // TOTP is set up, go to login
          setStep('login')
        } else {
          // Might need setup, show generate option
          setStep('generate')
        }
      }
    } catch (err: any) {
      // Assume needs setup
      setStep('generate')
    } finally {
      setLoading(false)
    }
  }

  const handleGenerateSecret = async () => {
    setError('')
    setSuccess('')
    setLoading(true)

    try {
      const response = await generateTotpSecret()
      if (response.success && response.secret) {
        setTotpSecret(response)
        setSuccess('TOTP secret generated! Scan the QR code with your authenticator app.')
        setStep('enable')
      } else {
        setError(response.message || 'Failed to generate TOTP secret')
        // If generation failed, TOTP might already be enabled
        if (response.message?.includes('already')) {
          setStep('login')
        }
      }
    } catch (err: any) {
      const errorMsg = err.response?.data?.message || err.message || 'Network error'
      // Check if error suggests TOTP is already enabled
      if (errorMsg.includes('already') || errorMsg.includes('enabled')) {
        setSuccess('TOTP already enabled. Proceeding to login...')
        setTimeout(() => setStep('login'), 1500)
      } else {
        setError(errorMsg)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleEnableTotp = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (!totp || totp.length !== 6) {
      setError('Please enter the 6-digit TOTP code')
      setLoading(false)
      return
    }

    if (!mpin || mpin.length !== 4) {
      setError('Please enter your 4-digit MPIN')
      setLoading(false)
      return
    }

    try {
      const response = await enableTotp({ totp, mpin })
      if (response.success) {
        setSuccess('TOTP enabled successfully! You can now login.')
        setTotp('')
        setMpin('')
        setTimeout(() => setStep('login'), 2000)
      } else {
        setError(response.message || 'Failed to enable TOTP')
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setSuccess('')
    setLoading(true)

    if (!totp || totp.length !== 6) {
      setError('Please enter the 6-digit TOTP code')
      setLoading(false)
      return
    }

    try {
      const response = await nubraLogin({ totp })

      if (response.success && response.session_id) {
        setSuccess('Successfully authenticated!')
        setAuthenticated(response.session_id)
        setTimeout(() => navigate('/'), 1500)
      } else {
        setError(response.message || 'Authentication failed')
      }
    } catch (err: any) {
      setError(err.response?.data?.message || 'Network error. Please try again.')
    } finally {
      setLoading(false)
    }
  }

  if (step === 'check') {
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
      <div className="w-full max-w-md space-y-6 p-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
            {step === 'generate' ? <Key className="h-8 w-8 text-primary" /> : <Lock className="h-8 w-8 text-primary" />}
          </div>
          <h1 className="text-2xl font-bold">SimpleTrader</h1>
          <p className="mt-2 text-muted-foreground">
            {step === 'generate' && 'Set up TOTP Authentication'}
            {step === 'enable' && 'Verify TOTP Setup'}
            {step === 'login' && 'Login with TOTP'}
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

        {/* Step 1: Generate Secret */}
        {step === 'generate' && (
          <div className="space-y-4">
            <div className="p-4 bg-primary/5 border border-primary/10 rounded-lg">
              <h3 className="font-medium mb-2">First Time Setup</h3>
              <p className="text-sm text-muted-foreground mb-4">
                You need to set up TOTP (Time-based One-Time Password) authentication with your Nubra account.
              </p>
              <ol className="text-sm text-muted-foreground space-y-2 list-decimal list-inside">
                <li>Click "Generate Secret" below</li>
                <li>Scan the QR code with your authenticator app</li>
                <li>Enter the 6-digit code to verify setup</li>
              </ol>
            </div>

            <Button
              onClick={handleGenerateSecret}
              disabled={loading}
              className="w-full"
            >
              {loading ? 'Generating...' : 'Generate TOTP Secret'}
            </Button>

            <Button
              variant="ghost"
              onClick={() => setStep('login')}
              className="w-full"
            >
              Already Set Up? Login
            </Button>
          </div>
        )}

        {/* Step 2: Enable TOTP */}
        {step === 'enable' && totpSecret && (
          <form onSubmit={handleEnableTotp} className="space-y-4">
            <div className="p-4 bg-success/5 border border-success/20 rounded-lg space-y-3">
              <div className="flex items-center gap-2 text-success">
                <CheckCircle className="h-5 w-5" />
                <p className="font-medium">Secret Generated!</p>
              </div>

              <div className="space-y-2">
                <p className="text-sm font-medium">Your Secret Key:</p>
                <code className="block p-2 bg-background rounded border text-xs break-all">
                  {totpSecret.secret}
                </code>
              </div>

              {totpSecret.qr_url && (
                <div className="space-y-2">
                  <p className="text-sm font-medium">Or Scan QR Code:</p>
                  <div className="flex justify-center p-4 bg-white rounded">
                    <img
                      src={`https://api.qrserver.com/v1/create-qr-code/?size=200x200&data=${encodeURIComponent(totpSecret.qr_url)}`}
                      alt="TOTP QR Code"
                      className="w-48 h-48"
                    />
                  </div>
                </div>
              )}
            </div>

            <div className="space-y-3">
              <div>
                <label htmlFor="totp" className="text-sm font-medium block mb-1">
                  TOTP Code from App
                </label>
                <Input
                  id="totp"
                  type="text"
                  placeholder="000000"
                  value={totp}
                  onChange={(e) => setTotp(e.target.value.replace(/\D/g, ''))}
                  maxLength={6}
                  className="text-center text-2xl font-mono tracking-widest"
                  autoFocus
                />
              </div>

              <div>
                <label htmlFor="mpin" className="text-sm font-medium block mb-1">
                  Your MPIN (4 digits)
                </label>
                <Input
                  id="mpin"
                  type="password"
                  placeholder="••••"
                  value={mpin}
                  onChange={(e) => setMpin(e.target.value.replace(/\D/g, ''))}
                  maxLength={4}
                  className="text-center text-2xl font-mono tracking-widest"
                />
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Verifying...' : 'Enable TOTP'}
            </Button>
          </form>
        )}

        {/* Step 3: Login with TOTP */}
        {step === 'login' && (
          <form onSubmit={handleLogin} className="space-y-4">
            <div className="space-y-2">
              <label htmlFor="totp-login" className="text-sm font-medium block">
                TOTP Code
              </label>
              <Input
                id="totp-login"
                type="text"
                placeholder="000000"
                value={totp}
                onChange={(e) => setTotp(e.target.value.replace(/\D/g, ''))}
                maxLength={6}
                className="text-center text-2xl font-mono tracking-widest"
                autoComplete="one-time-code"
                autoFocus
              />
              <p className="text-xs text-muted-foreground">
                Enter the 6-digit code from your authenticator app
              </p>
            </div>

            <Button type="submit" className="w-full" disabled={loading}>
              {loading ? 'Authenticating...' : 'Sign In with TOTP'}
            </Button>

            <Button
              type="button"
              variant="ghost"
              onClick={() => setStep('generate')}
              className="w-full"
            >
              Need to Set Up TOTP?
            </Button>
          </form>
        )}

        <div className="text-center text-xs text-muted-foreground space-y-1">
          <p>Use Google Authenticator, Authy, or any TOTP app</p>
          <p>Your session will persist for several days</p>
        </div>
      </div>
    </div>
  )
}
