import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import { Lock } from 'lucide-react'
import { Button } from '@/components/ui/Button'
import { Input } from '@/components/ui/Input'
import { useAuthStore } from '@/stores/authStore'

export default function Auth() {
  const [mpin, setMpin] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  const login = useAuthStore((state) => state.login)
  const navigate = useNavigate()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    if (!mpin || mpin.length < 4) {
      setError('Please enter a valid MPIN')
      setLoading(false)
      return
    }

    const success = await login(mpin)
    if (success) {
      navigate('/')
    } else {
      setError('Invalid MPIN')
    }
    setLoading(false)
  }

  return (
    <div className="flex h-screen w-full items-center justify-center bg-background">
      <div className="w-full max-w-md space-y-8 p-8">
        <div className="text-center">
          <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-full bg-primary/20">
            <Lock className="h-8 w-8 text-primary" />
          </div>
          <h1 className="text-2xl font-bold">SimpleTrader</h1>
          <p className="mt-2 text-muted-foreground">Sign in to your trading account</p>
        </div>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label htmlFor="mpin" className="text-sm font-medium">
              MPIN
            </label>
            <Input
              id="mpin"
              type="password"
              placeholder="Enter your MPIN"
              value={mpin}
              onChange={(e) => setMpin(e.target.value)}
              maxLength={6}
              className="mt-1"
              autoComplete="off"
            />
          </div>

          {error && (
            <p className="text-sm text-error">{error}</p>
          )}

          <Button type="submit" className="w-full" loading={loading}>
            Sign In
          </Button>
        </form>

        <p className="text-center text-xs text-muted-foreground">
          Credentials are processed securely and never stored on disk
        </p>
      </div>
    </div>
  )
}
