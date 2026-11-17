import { useState } from 'react'
import { Link, Navigate, useLocation, useNavigate } from 'react-router-dom'
import { ArrowRight, Eye, EyeOff, Sparkles } from 'lucide-react'
import { useAuth } from '../context/AuthContext'
import { useToast } from '../context/ToastContext'
import { AuthLayout } from '../components/AuthLayout'

export function LoginPage() {
  const { user, login } = useAuth()
  const { push } = useToast()
  const navigate = useNavigate()
  const location = useLocation()
  const from = (location.state as { from?: string } | null)?.from || '/'
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')

  if (user) return <Navigate to={user.is_admin ? '/admin' : from} replace />

  const signIn = async (emailValue: string, passwordValue: string) => {
    setLoading(true)
    setError('')
    try {
      const signedIn = await login(emailValue, passwordValue)
      push(`Welcome back, ${signedIn.name.split(' ')[0]}.`, 'success')
      navigate(signedIn.is_admin ? '/admin' : from, { replace: true })
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Could not sign you in.')
    } finally {
      setLoading(false)
    }
  }

  const submit = (event: React.FormEvent) => {
    event.preventDefault()
    void signIn(email, password)
  }

  const demo = (admin = false) => {
    const demoEmail = admin ? 'admin@shopwise.com' : 'demo@shopwise.com'
    const demoPassword = admin ? 'admin1234' : 'demo1234'
    setEmail(demoEmail)
    setPassword(demoPassword)
    void signIn(demoEmail, demoPassword)
  }

  return (
    <AuthLayout
      eyebrow="Welcome back"
      title={<>Good to see<br /><em>you again.</em></>}
      subtitle="Sign in to see your recommendations, revisit your orders and pick up where you left off."
    >
      <form className="auth-form" onSubmit={submit}>
        <label className="field">
          <span>Email address</span>
          <input type="email" value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@example.com" autoComplete="email" required />
        </label>
        <label className="field">
          <span>Password</span>
          <div className="password-field">
            <input type={showPassword ? 'text' : 'password'} value={password} onChange={(e) => setPassword(e.target.value)} placeholder="Your password" autoComplete="current-password" required />
            <button type="button" onClick={() => setShowPassword((value) => !value)} aria-label={showPassword ? 'Hide password' : 'Show password'}>
              {showPassword ? <EyeOff size={17} /> : <Eye size={17} />}
            </button>
          </div>
        </label>
        {error && <p className="auth-error">{error}</p>}
        <button type="submit" className="button button--dark button--full" disabled={loading}>
          {loading ? <span className="btn-spinner" /> : null}
          {loading ? 'Signing in…' : 'Sign in'} {!loading && <ArrowRight size={16} />}
        </button>
      </form>

      <div className="demo-box">
        <div className="demo-box__head"><Sparkles size={15} /><span>Try the demo account</span></div>
        <p>An account with a real purchase history, ready for personalised recommendations.</p>
        <div className="demo-box__credentials">
          <span><small>Email</small> demo@shopwise.com</span>
          <span><small>Password</small> demo1234</span>
        </div>
        <div className="demo-box__actions">
          <button className="button button--outline button--small" onClick={() => demo(false)} disabled={loading}>Enter as shopper</button>
          <button className="text-link" onClick={() => demo(true)} disabled={loading}>Admin demo <ArrowRight size={13} /></button>
        </div>
      </div>

      <p className="auth-switch">New to Shopwise? <Link to="/register">Create an account</Link></p>
    </AuthLayout>
  )
}
