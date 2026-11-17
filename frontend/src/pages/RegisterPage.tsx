import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, Gift } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { AuthLayout } from '../components/AuthLayout'

export function RegisterPage() {
  const { user, register } = useAuth()
  const { push } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from || '/'
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirm, setConfirm] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to={from} replace />

  const submit = async (event: React.FormEvent) => {
    event.preventDefault()
    setError('')
    if (password.length < 6) {
      setError('Choose a password of at least 6 characters.')
      return
    }
    if (password !== confirm) {
      setError('Those passwords do not match yet.')
      return
    }
    setLoading(true)
    try {
      const signedIn = await register(name, email, password)
      push(`Welcome to Shopwise, ${signedIn.name.split(' ')[0]}.`, 'success')
      navigate(from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not create your account.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <AuthLayout
      eyebrow="Join the shop"
      title={<>A shop that<br /><em>gets to know you.</em></>}
      subtitle="Create an account to save your bag, follow your orders and unlock recommendations made for you."
      image="/static/auth-visual.svg"
      quote="Recommendations should feel like a knowledgeable friend, not a billboard."
    >
      <form className="auth-form" onSubmit={submit}>
        <label className="field">
          <span>Your name</span>
          <input value={name} onChange={(e) => setName(e.target.value)} placeholder="Sofia Hart" autoComplete="name" required minLength={2} />
        </label>
        <label className="field">
          <span>Email address</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />
        </label>
        <div className="form-grid">
          <label className="field">
            <span>Password</span>
            <div className="password-field">
              <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="At least 6 characters" autoComplete="new-password" required minLength={6} />
              <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
                {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
              </button>
            </div>
          </label>
          <label className="field">
            <span>Confirm password</span>
            <input type={showPassword ? 'text' : 'password'} value={confirm} onChange={(e) => setConfirm(e.target.value)} placeholder="Same again" autoComplete="new-password" required />
          </label>
        </div>
        {error && <p className="auth-error">{error}</p>}
        <label className="checkbox-row">
          <input type="checkbox" />
          <span>Send me occasional notes, new arrivals and a birthday treat.</span>
        </label>
        <button type="submit" className="button button--dark button--full" disabled={loading}>
          {loading ? <span className="btn-spinner" /> : <Gift size={16} />}
          {loading ? 'Creating your account…' : 'Create my account'} {!loading && <ArrowRight size={16} />}
        </button>
      </form>
      <p className="auth-switch">Already have an account? <Link to="/login">Sign in</Link></p>
    </AuthLayout>
  )
}
